// admin.js
admin = db.getSiblingDB("admin")

// creation of the database admin user
admin.createUser(
  {
    user: "{{ db_admin_user }}",
    pwd: "{{ db_admin_pass }}",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
  }
)

// let's authenticate to create the other user
db.getSiblingDB("admin").auth("{{ db_admin_user }}", "{{ db_admin_pass }}")

// creation of the replica set admin user
db.getSiblingDB("admin").createUser(
  {
    "user" : "{{ replica_admin_user }}",
    "pwd" : "{{ replica_admin_pass }}",
    roles: [ { "role" : "clusterAdmin", "db" : "admin" } ]
  }
)