import sys
from awsglue.transforms import *
from pyspark.sql.functions import current_timestamp, to_timestamp
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from datetime import datetime

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Pull data from catalog
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="database-name", 
    table_name="document"
)

# Convert to DataFrame
df = datasource.toDF()

# Get today partition
today_ = '{:02d}'.format(datetime.now().year) + '{:02d}'.format(datetime.now().month) + '{:02d}'.format(datetime.now().day)
df_filtered = df.filter(df.dataloader == today_)

# Make sure the columns to be casted explicitly
df_filtered = df_filtered.withColumn("created", to_timestamp("created", "MM-dd-yyyy HH:mm:ss"))
df_filtered = df_filtered.withColumn("updated", to_timestamp("updated", "MM-dd-yyyy HH:mm:ss"))

# Drop partition column
df_filtered = df_filtered.drop(*['dataloader'])

# Add added column to timestamp when the data is added
df_filtered = df_filtered.withColumn("added", current_timestamp().cast("timestamp"))

# PostgreSQL JDBC connection info
jdbc_url = "jdbc:postgresql://RDS-Instance:5432/database-name"
connection_properties = {
    "user": "user",
    "password": "password",
    "driver": "org.postgresql.Driver"
}

# Load existing data from PostgreSQL
existing_document_df = spark.read.jdbc(
    url=jdbc_url,
    table="document",
    properties=connection_properties
)

# unique identifier is called 'id'
join_key = 'id'

# Left Join: Find new documents that are not in the existing data (INSERTS)
new_document_df = df_filtered.join(existing_document_df, join_key, "left_anti")

# Write new documents to the PostgreSQL table using JDBC
new_document_df.write.jdbc(
    url=jdbc_url,
    table="document",
    mode="append",  # We only want to append new records
    properties=connection_properties
)

job.commit()