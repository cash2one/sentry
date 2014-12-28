{
  "_context_roles": [
    "admin"
  ], 
  "_context_request_id": "req-fe58c1d5-9de8-43d7-858d-51f9e6565102", 
  "_context_read_deleted": "no", 
  "event_type": "subnet.create.end", 
  "_context_user_name": "admin", 
  "timestamp": "2014-12-27 09:53:27.891128", 
  "_context_tenant_name": "admin", 
  "_context_tenant": "5944f796796141c99b032294116cb52e", 
  "message_id": "7bd277ef-4a36-460c-9ada-68da029ffefd", 
  "_unique_id": "1bc726c7d66e4795aa509ebe381433c6", 
  "_context_is_admin": true, 
  "_context_timestamp": "2014-12-27 09:53:27.441780", 
  "_context_project_id": "5944f796796141c99b032294116cb52e", 
  "_context_tenant_id": "5944f796796141c99b032294116cb52e", 
  "_context_user": "a133807120664049b8df4e5a16b7ddf4", 
  "_context_user_id": "a133807120664049b8df4e5a16b7ddf4", 
  "publisher_id": "network.binjiang-neutron-netease", 
  "payload": {
    "subnets": [
      {
        "name": "subnet--tempest-2007574076", 
        "enable_dhcp": true, 
        "network_id": "f96679d5-fd40-4fe5-bcf0-7c88e1f45f2d", 
        "tenant_id": "5944f796796141c99b032294116cb52e", 
        "dns_nameservers": [], 
        "enable_dns": true, 
        "allocation_pools": [
          {
            "start": "10.100.0.2", 
            "end": "10.100.0.14"
          }
        ], 
        "host_routes": [], 
        "ip_version": 4, 
        "gateway_ip": "10.100.0.1", 
        "cidr": "10.100.0.0/28", 
        "id": "0593afd7-55ea-4298-87aa-86686d03cd68"
      }, 
      {
        "name": "", 
        "enable_dhcp": true, 
        "network_id": "0fcfabed-65ad-4bdd-a489-2a1f0e499c29", 
        "tenant_id": "5944f796796141c99b032294116cb52e", 
        "dns_nameservers": [], 
        "enable_dns": true, 
        "allocation_pools": [
          {
            "start": "10.100.0.18", 
            "end": "10.100.0.30"
          }
        ], 
        "host_routes": [], 
        "ip_version": 4, 
        "gateway_ip": "10.100.0.17", 
        "cidr": "10.100.0.16/28", 
        "id": "a6e48c2f-c3b3-4621-be6f-be853a43435e"
      }
    ]
  }, 
  "priority": "INFO"
}
