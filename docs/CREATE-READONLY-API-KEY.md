# Create the read-only API key for the source cluster

Organizer-only, done once. Participants never run this: they get the key and the source cluster URL during the session and paste them into the `_reindex` commands in the [README](../README.md#-get-the-data) (or [`reindex-all.kibana.txt`](reindex-all.kibana.txt)).

Run it in **Kibana Dev Tools** on the **source** cluster, the one holding the `f1-*-lite` indices.

```js
POST /_security/api_key
{
  "name": "f1-hackathon-readonly",
  "expiration": "7d",
  "role_descriptors": {
    "f1-lite-reader": {
      "cluster": ["monitor"],
      "indices": [
        {
          "names": ["f1-*-lite"],
          "privileges": ["read", "view_index_metadata"]
        }
      ]
    }
  },
  "metadata": { "purpose": "hackathon remote reindex, read-only" }
}
```

What the key allows:

- `read` and `view_index_metadata` on `f1-*-lite`: one key for all five indices (and any `f1-*-lite` index added later), no writes.
- `monitor` (cluster): required. Remote reindex reads the source's root endpoint to detect the source version, and without `monitor` the reindex is refused. It also lets participants check document counts with `_cat/indices`. It is read-only.

If a key was already created without `monitor`, update it in place on the **source** cluster (the key value does not change):

```js
PUT /_security/api_key/<KEY_ID>
{
  "role_descriptors": {
    "f1-lite-reader": {
      "cluster": ["monitor"],
      "indices": [
        { "names": ["f1-*-lite"], "privileges": ["read", "view_index_metadata"] }
      ]
    }
  }
}
```

If the update is refused, create a new key with the `POST` above, share its `encoded` value, and revoke the old one (see the end of this page).

The response looks like this:

```json
{
  "id": "VuaCfGcBCdbkQm-e5aOx",
  "name": "f1-hackathon-readonly",
  "expiration": 1761000000000,
  "api_key": "ui2lp2axTNmsyakw9tvNnw",
  "encoded": "VnVhQ2ZHY0JDZGJrUW0tZTVhT3g6dWkybHAyYXhUTm1zeWFrdzl0dk5udw=="
}
```

Share the **`encoded`** value (not `api_key`) as `<ELASTICSEARCH_API_KEY>`, and the source cluster's Elasticsearch endpoint (for example `https://my-deployment.es.eu-west-1.aws.found.io:443`) as `<SOURCE_CLUSTER_URL>`.

## How the renaming works

The key does not rename anything. Each `_reindex` command reads `f1-<name>-lite` from the source and writes to `dest.index: f1-<name>`, so `f1-telemetry-lite` becomes `f1-telemetry` on the participant's cluster.

## Verify

With the new key, from a destination cluster:

```js
POST _reindex?wait_for_completion=false
{
  "source": {
    "remote": { "host": "<SOURCE_CLUSTER_URL>", "api_key": "<ENCODED_KEY>" },
    "index": "f1-sessions-lite"
  },
  "dest": { "index": "f1-sessions" }
}
```

Expected counts afterwards: `GET _cat/indices/f1-*?v&h=index,docs.count&s=index` returns f1-laps 3531, f1-results 80, f1-sessions 4, f1-telemetry 2869213, f1-weather 541.

## Destination requirements

The destination cluster must be allowed to reindex from the source host: on self-managed, add it to `reindex.remote.whitelist` in `elasticsearch.yml`; on Elastic Cloud Hosted, add it under **Edit > Manage user settings and extensions**.

## Revoke after the event

```js
DELETE /_security/api_key
{ "name": "f1-hackathon-readonly" }
```
