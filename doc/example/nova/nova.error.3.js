{
  "_context_request_id": "req-fd77bb0e-257a-4459-a6a4-0ea4aedc8358", 
  "_context_quota_class": null, 
  "event_type": "create_aggregate", 
  "_context_service_catalog": [
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
  "_context_auth_token": "35a54a1d239742f3a36b1fb93e74eb14", 
  "_context_user_id": "ebb67235828d40f6a4e0db00c6cc5a6f", 
  "payload": {
    "exception": {
      "kwargs": {
        "code": 500, 
        "aggregate_name": "test_aggregate_-tempest-1827307756"
      }
    }, 
    "args": {
      "self": null, 
      "aggregate_name": "test_aggregate_-tempest-1827307756", 
      "context": {
        "project_name": "admin", 
        "user_id": "ebb67235828d40f6a4e0db00c6cc5a6f", 
        "roles": [
          "admin"
        ], 
        "_read_deleted": "no", 
        "timestamp": "2014-12-31T13:58:05.417425", 
        "auth_token": "35a54a1d239742f3a36b1fb93e74eb14", 
        "remote_address": "10.166.224.8", 
        "quota_class": null, 
        "is_admin": true, 
        "service_catalog": [
          {
            "endpoints": [
              {
                "adminURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad", 
                "region": "RegionOne", 
                "internalURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad", 
                "id": "4eb84e99530a45928f021ad531be166f", 
                "publicURL": "http://10.166.224.8:8776/v1/a2896e2e1b2b45a0bb2736e7f57d93ad"
              }
            ], 
            "endpoints_links": [], 
            "type": "volume", 
            "name": "cinder"
          }
        ], 
        "request_id": "req-fd77bb0e-257a-4459-a6a4-0ea4aedc8358", 
        "instance_lock_checked": false, 
        "project_id": "a2896e2e1b2b45a0bb2736e7f57d93ad", 
        "user_name": "admin"
      }, 
      "availability_zone": null
    }
  }, 
  "priority": "ERROR", 
  "_context_is_admin": true, 
  "_context_user": "ebb67235828d40f6a4e0db00c6cc5a6f", 
  "publisher_id": "compute.netease-havana", 
  "message_id": "0be99ad9-ef14-4632-8a7f-8dabd132bd62", 
  "_context_remote_address": "10.166.224.8", 
  "_context_roles": [
    "admin"
  ], 
  "timestamp": "2014-12-31 13:58:05.475539", 
  "_context_timestamp": "2014-12-31T13:58:05.417425", 
  "_unique_id": "92846a41b24b49ccac315974060d99a3", 
  "_context_project_name": "admin", 
  "_context_read_deleted": "no", 
  "_context_tenant": "a2896e2e1b2b45a0bb2736e7f57d93ad", 
  "_context_instance_lock_checked": false, 
  "_context_project_id": "a2896e2e1b2b45a0bb2736e7f57d93ad", 
  "_context_user_name": "admin"
}
