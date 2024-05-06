from django.db import models
from user_group_management.models import User, Group
from django.contrib.postgres.fields import JSONField
from datetime import datetime

class Connectiondata(models.Model):
    PERSONAL = 1
    GROUP = 2
    ORGANIZATION = 3
    PUBLIC = 4
    PUBLISH_TYPE = (
        (PERSONAL, 'Personal'),
        (GROUP, 'Group'),
        (ORGANIZATION, 'Organization'),
        (PUBLIC, 'Public'),
    )
    meta_id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connection_owner')
    database_type = models.CharField(max_length=50)
    publish_status = models.SmallIntegerField(choices=PUBLISH_TYPE, default=PERSONAL)
    publish_to_group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    database_name = models.CharField(max_length=50)
    connection_details = models.JSONField()


class Tabledata(models.Model):
    QUEUED = 1
    RUNNING = 2
    SUCCESS = 3
    FAILED = 4
    ETL_STATUS = (
        (QUEUED, "Queued"),
        (RUNNING, "Running"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    )
    table_id = models.BigAutoField(primary_key=True)
    metadata = models.ForeignKey(Connectiondata, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50)
    etl_pass = models.IntegerField(default=0)
    etl_fail = models.IntegerField(default=0)
    etl_abort = models.IntegerField(default=0)
    test_pass = models.IntegerField(default=0)
    test_fail = models.IntegerField(default=0)
    test_abort = models.IntegerField(default=0)
    inserted_data = models.JSONField(null=True)
    deleted_data = models.JSONField(null=True)
    scheduled = models.CharField(max_length=30)
    dag_run_id = models.TextField(null=True, blank=True)
    dag_id = models.CharField(null=True, blank=True)
    status = models.SmallIntegerField(choices=ETL_STATUS, default=QUEUED)

    def __str__(self) -> str:
        return self.name
    

class Columndata(models.Model):
    column_id = models.BigAutoField(primary_key=True)
    table = models.ForeignKey(Tabledata, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=50)
    datatype = models.CharField(max_length=30)
    last_data = models.JSONField(null=True)
    test_pass = models.IntegerField(default=0)
    test_fail = models.IntegerField(default=0)
    test_abort = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class Metric(models.Model):
    matric_id = models.BigAutoField(primary_key=True)
    table = models.ForeignKey(Tabledata, on_delete=models.CASCADE, related_name='metric')
    row_count = models.IntegerField(default=0)
    col_count = models.IntegerField(default=0)
    size = models.BigIntegerField(default=0)
    metric_value = models.JSONField()
    timestamp = models.DateTimeField(default=datetime.now)


class Test(models.Model):
    TABLE = 1
    COLUMN = 2
    TEST_TYPE = (
        (TABLE, 'Table'),
        (COLUMN, 'Column')
    )
    test_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    test_purpose = models.CharField(blank=True, null=True)
    test_purpose_value = models.JSONField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    test_type = models.SmallIntegerField(choices=TEST_TYPE, default=TABLE)
    dag_run_id = models.TextField(null=True, blank=True)
    status = models.SmallIntegerField(choices=Tabledata.ETL_STATUS, default=Tabledata.QUEUED)
    table = models.ForeignKey(Tabledata, null=True, blank=True, on_delete=models.CASCADE, related_name='test_table')
    column = models.ForeignKey(Columndata, null=True, blank=True, on_delete=models.CASCADE, related_name='test_column')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_owner')
    timestamp = models.DateTimeField(default=datetime.now)
