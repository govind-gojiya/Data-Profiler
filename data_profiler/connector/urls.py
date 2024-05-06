from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("dashboard", views.dashboard, name="home_page"),
    path('connector', views.connector_form, name='provide_connector_form'),
    path('add_connector_data', views.add_connector_data, name='add_connector_data'),
    path('get_table_data/<int:meta_id>', views.get_table_data, name='get_table_data'),
    path('remove_connector_details/<int:meta_id>', views.remove_connector_details, name='remove_connector_details'),
    path('run_etl_for_table/<int:meta_id>', views.run_etl_for_table, name='run_etl_for_table'),
    path('connector/get_last_etl_logs', views.get_last_etl_logs, name='get_last_etl_logs'),
    path('connector/get_current_data_of_table', views.get_current_data, name="get_current_data_of_table"),
    path('test/get_all_connectors', views.get_all_connectors, name="get_all_conn_to_test"),
    path('test/get_test_form/<int:meta_id>', views.get_test_form, name='get_test_form'),
    path('test/get_testcase_for_form/', views.get_testcase_for_form, name='get_testcase_for_form'),
    path('test/add_test', views.add_test, name='add_test'),
    path('test/get_all_tests_performed', views.get_all_tests_performed, name='get_all_tests_performed'),
    path('run_etl_for_connector/<int:meta_id>', views.run_etl_for_connector, name="run_etl_for_connector"),
    path('connector/chat_with_data', views.chat_with_data, name='chat_with_data'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)