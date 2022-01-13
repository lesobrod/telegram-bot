import redis
# data_base_name ='HeartTravel'
# TODO Пароль в системную переменную
# endpoint redis-17913.c281.us-east-1-2.ec2.cloud.redislabs.com:17913
redis_db = redis.StrictRedis(
    host='redis-17913.c281.us-east-1-2.ec2.cloud.redislabs.com',
    port=17913,
    password='7PYOiVZ7P1jLRPqKJdVk01KHwCcttG8n',
    db=0,
    charset='utf-8',
    decode_responses=True
)
print(redis_db)
