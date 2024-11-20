import sys
from awsglue.transforms import *
from pyspark.sql.functions import col
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Pull data from csv file
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://Your-S3-bucket/database/user/users.csv/"]},
    format_options= {'withHeader': True},
    format="csv"
)

# Convert to DataFrame (if needed for complex operations)
df = datasource.toDF()

# Make sure the columns to be casted explicitly
df = df.withColumn("last_login_datetime", col("last_login_datetime").cast("timestamp"))
df = df.withColumn("created_at_datetime", col("created_at_datetime").cast("timestamp"))
df = df.withColumn("last_login", col("last_login").cast("bigint"))
df = df.withColumn("created_at", col("created_at").cast("bigint"))
df = df.withColumn("toexport", col("toexport").cast("boolean"))

# PostgreSQL JDBC connection info
jdbc_url = "jdbc:postgresql://RDS-Instance:5432/database-name"
connection_properties = {
    "user": "user",
    "password": "password",
    "driver": "org.postgresql.Driver"
}

# Load data to temp users table
df.write.jdbc(
    url=jdbc_url,
    table="public.temp_user",
    mode="overwrite",
    properties=connection_properties
)

job.commit()