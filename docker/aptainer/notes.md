
# mysql

```bash
echo "SET PASSWORD FOR 'root'@'localhost' = '<root_password>';" > mysqlrootpw

# to retain
mkdir -p ./mysql/var/lib/mysql/ ./mysql/run/mysqld

apptainer pull --name mysql.simg docker://mysql

apptainer instance start --bind ${PWD} --bind ${PWD}/mysql/var/lib/mysql/:/var/lib/mysql --bind ${PWD}/mysql/run/mysqld:/run/mysqld ./mysql.simg mysql

apptainer exec instance://mysql mysqld --initialize --init-file=${PWD}/mysqlrootpw
apptainer exec instance://mysql mysqld --port=23306 --init-file=${PWD}/mysqlrootpw

mysql -S mysql/run/mysqld/mysqld.sock -u root -p

apptainer shell instance://mysql
```
