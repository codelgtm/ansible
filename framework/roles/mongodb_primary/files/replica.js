//replica.js

rs.initiate({
 _id: '{{ replica_set }}',
 members: [{
  _id: 0, host: '{{ ansible_fqdn }}:{{ mongo_port }}'
 }]
})