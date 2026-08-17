from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import BloodStock, BloodRequest, LegacyBloodStock  # <-- Import from bloodbank
from .forms import StockForm, RequestForm

@login_required
def stock_list(request):
    # 1. New system stock
    new_stocks = BloodStock.objects.all()
    new_dict = {s.blood_group: s.quantity for s in new_stocks}
    
    # 2. Legacy system stock (Read-only, auto-routed to legacy DB)
    legacy_stocks = LegacyBloodStock.objects.all()
    legacy_dict = {l.blood_type: l.total_units for l in legacy_stocks}
    
    # 3. Combine
    all_groups = set(list(new_dict.keys()) + list(legacy_dict.keys()))
    combined_stock = []
    for group in sorted(all_groups):
        combined_stock.append({
            'blood_group': group,
            'new_qty': new_dict.get(group, 0),
            'legacy_qty': legacy_dict.get(group, 0),
            'total_qty': new_dict.get(group, 0) + legacy_dict.get(group, 0)
        })
    
    context = {
        'combined_stock': combined_stock,
        'total_units': sum([item['total_qty'] for item in combined_stock])
    }
    return render(request, 'stocks_list.html', context)


@login_required
def add_stock(request):
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            blood_group = form.cleaned_data['blood_group']
            quantity = form.cleaned_data['quantity']
            expiry_date = form.cleaned_data['expiry_date']

            stock, created = BloodStock.objects.get_or_create(blood_group=blood_group)
            stock.quantity += quantity
            if created or expiry_date > stock.expiry_date:
                stock.expiry_date = expiry_date
            stock.save()
            
            messages.success(request, f'Added {quantity} units of {blood_group} to NEW system.')
            return redirect('stock_list')
    else:
        form = StockForm()
    return render(request, 'add_stock.html', {'form': form})


@login_required
def request_blood(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            blood_group = form.cleaned_data['blood_group']
            quantity_needed = form.cleaned_data['quantity_needed']
            
            blood_request = form.save(commit=False)
            blood_request.status = 'pending'
            
            with transaction.atomic():
                try:
                    stock = BloodStock.objects.get(blood_group=blood_group)
                except BloodStock.DoesNotExist:
                    stock = None

                if stock and stock.quantity >= quantity_needed:
                    stock.quantity -= quantity_needed
                    stock.save()
                    blood_request.status = 'fulfilled'
                    blood_request.fulfilled_from = stock
                    messages.success(request, 'Request fulfilled from current stock!')
                else:
                    messages.info(request, 'Insufficient stock. Request marked as Pending for future.')
                
                blood_request.save()
            return redirect('request_list')
    else:
        form = RequestForm()
    return render(request, 'request_blood.html', {'form': form})


@login_required
def request_list(request):
    requests = BloodRequest.objects.all().order_by('-created_at')
    pending_count = requests.filter(status='pending').count()
    return render(request, 'request_list.html', {
        'requests': requests,
        'pending_count': pending_count
    })


@login_required
def fulfill_pending_request(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id, status='pending')
    stock = get_object_or_404(BloodStock, blood_group=blood_request.blood_group)
    
    if stock.quantity >= blood_request.quantity_needed:
        with transaction.atomic():
            stock.quantity -= blood_request.quantity_needed
            stock.save()
            blood_request.status = 'fulfilled'
            blood_request.fulfilled_from = stock
            blood_request.save()
        messages.success(request, f'Request #{request_id} fulfilled!')
    else:
        messages.error(request, f'Still insufficient! Available: {stock.quantity}')
    
    return redirect('request_list')


@login_required
def import_legacy_to_new(request):
    if request.method == 'POST':
        legacy_records = LegacyBloodStock.objects.all()
        imported_count = 0
        for legacy in legacy_records:
            stock, created = BloodStock.objects.get_or_create(
                blood_group=legacy.blood_type
            )
            stock.quantity += legacy.total_units
            if created or legacy.expiry > stock.expiry_date:
                stock.expiry_date = legacy.expiry
            stock.save()
            imported_count += 1
        
        messages.success(request, f'Successfully imported {imported_count} legacy stock entries!')
        return redirect('stock_list')
    
    legacy_data = LegacyBloodStock.objects.all()[:10]
    return render(request, 'import_confirm.html', {'legacy_data': legacy_data})