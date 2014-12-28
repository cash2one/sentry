{
  "_context_request_id": "req-20e30447-1021-4521-b49d-d08ae2ad6269", 
  "_context_quota_class": null, 
  "event_type": "add_host_to_aggregate", 
  "_context_service_catalog": [
    {
      "endpoints": [
        {
          "adminURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad", 
          "region": "RegionOne", 
          "id": "4eb84e99530a45928f021ad531be166f", 
          "internalURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad", 
          "publicURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad"
        }
      ], 
      "endpoints_links": [], 
      "type": "volume", 
      "name": "cinder"
    }
  ], 
  "_context_auth_token": "35a54a1d239742f3a36b1fb93e74eb14", 
  "_context_user_id": "ebb67235828d40f6a4e0db00c6cc5a6f", 
  "payload": {
    "exception": {
      "kwargs": {
        "host": "netease-havana", 
        "code": 500, 
        "aggregate_id": 1
      }
    }, 
    "args": {
      "self": null, 
      "host_name": "netease-havana", 
      "context": {
        "project_name": "admin", 
        "user_id": "ebb67235828d40f6a4e0db00c6cc5a6f", 
        "roles": [
          "admin"
        ], 
        "_read_deleted": "no", 
        "timestamp": "2014-12-31T13:58:03.625448", 
        "auth_token": "35a54a1d239742f3a36b1fb93e74eb14", 
        "remote_address": "10.166.224.8", 
        "quota_class": null, 
        "is_admin": true, 
        "service_catalog": [
          {
            "endpoints_links": [], 
            "endpoints": [
              {
                "adminURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad", 
                "region": "RegionOne", 
                "publicURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad", 
                "id": "4eb84e99530a45928f021ad531be166f", 
                "internalURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad"
              }
            ], 
            "type": "volume", 
            "name": "cinder"
          }
        ], 
        "request_id": "req-20e30447-1021-4521-b49d-d08ae2ad6269", 
        "instance_lock_checked": false, 
        "project_id": "a2896e2e1b2b45a0bb2736e7f57d93ad", 
        "user_name": "admin"
      }, 
      "aggregate_id": "1"
    }
  }, 
  "priority": "ERROR", 
  "_context_is_admin": true, 
  "_context_user": "ebb67235828d40f6a4e0db00c6cc5a6f", 
  "publisher_id": "compute.netease-havana", 
  "message_id": "bf113d8b-ccec-4873-8a49-fbf7a41ad788", 
  "_context_remote_address": "10.166.224.8", 
  "_context_roles": [
    "admin"
  ], 
  "timestamp": "2014-12-31 13:58:03.876742", 
  "_context_timestamp": "2014-12-31T13:58:03.625448", 
  "_unique_id": "f43952935cc64a22b564e9454d407be5", 
  "_context_project_name": "admin", 
  "_context_read_deleted": "no", 
  "_context_tenant": "a2896e2e1b2b45a0bb2736e7f57d93ad", 
  "_context_instance_lock_checked": false, 
  "_context_project_id": "a2896e2e1b2b45a0bb2736e7f57d93ad", 
  "_context_user_name": "admin"
}
