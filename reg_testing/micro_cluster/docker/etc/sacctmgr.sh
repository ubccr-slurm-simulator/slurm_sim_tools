# add/modify QOS
modify QOS set normal Priority=0
add QOS Name=supporters Priority=100
# add cluster
add cluster Name=micro Fairshare=1 QOS=normal,supporters
# add accounts
add account name=account0 Fairshare=100
add account name=account1 Fairshare=100
add account name=account2 Fairshare=100
# add admin
add user name=admin DefaultAccount=account0 MaxSubmitJobs=1000 AdminLevel=Administrator
# add users
add user name=user1 DefaultAccount=account1 MaxSubmitJobs=1000
add user name=user2 DefaultAccount=account1 MaxSubmitJobs=1000
add user name=user3 DefaultAccount=account1 MaxSubmitJobs=1000
add user name=user4 DefaultAccount=account2 MaxSubmitJobs=1000
add user name=user5 DefaultAccount=account2 MaxSubmitJobs=1000
# add users to qos level
modify user set qoslevel="normal,supporters"

# check results
list associations format=Account,Cluster,User,Fairshare tree withd