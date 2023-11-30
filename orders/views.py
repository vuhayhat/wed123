from django.shortcuts import render, redirect, Http404
from django.views import generic
from orders.forms import OrderForm
from orders.models import Order, OrderItem
from cart.cart import Cart
from django.db.models import Count
from store.models import Product
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse #
from django.http import JsonResponse #
from paypalrestsdk import Payment #
# Create your views here.


class CreateOrder(LoginRequiredMixin, generic.CreateView):
    form_class = OrderForm
    template_name = 'orders/place_order.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        products = Product.objects.filter(pk__in=cart.cart.keys())
        cart_items = map(
            lambda p: {'product': p, 'quantity': cart.cart[str(p.id)]['quantity'], 'total': p.price*cart.cart[str(p.id)]['quantity']}, products)
        context['summary'] = cart_items
        return context

    def form_valid(self, form):
        cart = Cart(self.request)
        if len(cart) == 0:
            return redirect('cart:cart_details')
        order = form.save(commit=False)
        order.user = self.request.user
        order.total_price = cart.get_total_price()
        order.save()
        products = Product.objects.filter(id__in=cart.cart.keys())
        orderitems = []
        for i in products:
            q = cart.cart[str(i.id)]['quantity']
            orderitems.append(
                OrderItem(order=order, product=i, quantity=q, total=q*i.price))
        OrderItem.objects.bulk_create(orderitems)
        cart.clear()
        messages.success(self.request, 'Your order is successfully placed.')
        return redirect('store:product_list')


class MyOrders(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).annotate(total_items=Count('items'))


class OrderDetails(LoginRequiredMixin, generic.DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'orders/order_details.html'

    def get_queryset(self, **kwargs):
        objs = super().get_queryset(**kwargs)
        return objs.filter(user=self.request.user).prefetch_related('items', 'items__product')


class OrderInvoice(LoginRequiredMixin, generic.DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'orders/order_invoice.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related('items', 'items__product')

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        if obj.user_id == self.request.user.id or self.request.user.is_superuser:
            return obj
        raise Http404


# Add the following imports at the beginning of your views.py file
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def create_payment(request, order_id):
    # Replace these values with your PayPal API credentials
    client_id = 'YOUR_PAYPAL_CLIENT_ID'
    client_secret = 'YOUR_PAYPAL_CLIENT_SECRET'

    paypalrestsdk.configure({
        "mode": "sandbox",  # Set to "live" for production
        "client_id": client_id,
        "client_secret": client_secret,
    })

    order = get_your_order_function(order_id)  # Replace with your actual function to get the order

    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal",
        },
        "redirect_urls": {
            "return_url": request.build_absolute_uri(reverse('paypal_execute')),
            "cancel_url": request.build_absolute_uri(reverse('paypal_cancel')),
        },
        "transactions": [
            {
                "item_list": {
                    "items": [
                        {
                            "name": item.product.name,
                            "sku": str(item.product.id),
                            "price": str(item.product.price),
                            "currency": "USD",  # Change currency as needed
                            "quantity": item.quantity,
                        } for item in order.items.all()
                    ],
                },
                "amount": {
                    "total": str(order.total_price),
                    "currency": "USD",  # Change currency as needed
                },
                "description": "Payment for Order #{}".format(order.id),
            },
        ],
    })

    if payment.create():
        approval_url = next(link.href for link in payment.links if link.rel == 'approval_url')
        return redirect(approval_url)
    else:
        return JsonResponse({'error': payment.error})

@csrf_exempt
def execute_payment(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        # Payment executed successfully
        return render(request, 'payment_success.html')
    else:
        return JsonResponse({'error': payment.error})

def cancel_payment(request):
    return render(request, 'payment_cancel.html')