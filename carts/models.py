from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save, m2m_changed

from products.models import Product


User = settings.AUTH_USER_MODEL

class CartManager(models.Manager):
    """
    model manager for cart table
    """
    def new_or_get(self, request):
        cart_id = request.session.get("cart_id", None)
        qs = self.get_queryset().filter(id=cart_id)
        if qs.count() == 1:
            new_obj = False
            cart_obj = qs.first()
            if request.user.is_authenticated and cart_obj.user is None:
                cart_obj.user = request.user
                cart_obj.save()
        else:
            cart_obj = Cart.objects.new(user=request.user)
            new_obj = True
            request.session['cart_id'] = cart_obj.id
        return cart_obj, new_obj

    def new(self, user=None):
        user_obj = None
        if user is not None:
            if user.is_authenticated:
                user_obj = user
        return self.model.objects.create(user=user_obj)

class Cart(models.Model):
    """
    cart model
    """
    user        = models.ForeignKey(User, null=True, blank=True,  on_delete = models.CASCADE)
    products    = models.ManyToManyField(Product, blank=True)
    gst_total   = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    subtotal    = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    total       = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    updated     = models.DateTimeField(auto_now=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    objects = CartManager()

    def __str__(self):
        return str(self.id)

    @property
    def is_digital(self):
        qs = self.products.all() #every product
        new_qs = qs.filter(is_digital=False) # every product that is not digial
        if new_qs.exists():
            return False
        return True




def m2m_changed_cart_receiver(sender, instance, action, *args, **kwargs):
    """
    signal for whenver user add or remove product from cart, this will run so that we can get
    the new cart total
    """
    if action == 'post_add' or action == 'post_remove' or action == 'post_clear':
        products = instance.products.all()
        total = 0
        sub_total = 0
        gst_total = 0
        for x in products:
            gst = (x.price//100)*(x.gst_percentage)
            sub_total = sub_total + x.price
            total = total + gst + x.price
            gst_total = gst_total + gst
    

            instance.total = total
            instance.save()

            instance.subtotal = sub_total
            instance.save()

            instance.gst_total = gst_total
            instance.save()

            print("subtotal", sub_total)
            print("total", total)
            print("gst total", gst_total)

        # if instance.subtotal != total:
        #     instance.subtotal = total
        #     instance.save()


# def m2m_changed_cart_receiver(sender, instance, action, *args, **kwargs):
#     if action == 'post_add' or action == 'post_remove' or action == 'post_clear':
#         products = instance.products.all()
#         total = 0
#         sub_total = 0
#         gst_total = 0
#         for x in products:
#             total += x.price
#         if instance.subtotal != total:
#             instance.subtotal = total
#             instance.save()

m2m_changed.connect(m2m_changed_cart_receiver, sender=Cart.products.through)




# def pre_save_cart_receiver(sender, instance, *args, **kwargs):
#     if instance.subtotal > 0:
#         instance.total = Decimal(instance.subtotal) * Decimal(1.08) # 8% tax
#     else:
#         instance.total = 0.00

# pre_save.connect(pre_save_cart_receiver, sender=Cart)









