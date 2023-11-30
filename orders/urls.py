from django.urls import path
from orders import views
from .views import create_payment, execute_payment, cancel_payment
#from .views import XacNhanDonHangView #thêm vào
app_name = 'orders'
urlpatterns = [
    path('place', views.CreateOrder.as_view(), name='place'),
    path('my', views.MyOrders.as_view(), name='my'),
    path('details/<int:pk>/', views.OrderDetails.as_view(), name='details'),
    path('invoice/<int:pk>/', views.OrderInvoice.as_view(), name='invoice'),
   # path('xac-nhan-don-hang/<int:pk>/', XacNhanDonHangView.as_view(), name='tenduongdanxacnhandonhang'),
    path('create_payment/<int:order_id>/', create_payment, name='create_payment'),
    path('execute_payment/', execute_payment, name='paypal_execute'),
    path('cancel_payment/', cancel_payment, name='paypal_cancel'),
    # Other URLs...
]


