import csv

def generate_csv(response, tenant_payments):
    writer = csv.writer(response)
    writer.writerow(['#', 'Tenant', 'House No.', 'Amount Paid', 'Payment Method', 'Payment Date', 'Month', 'Year', 'Payment Type'])
    for count, payment in enumerate(tenant_payments, start=1):
        writer.writerow([
            count,
            payment.tenant.user.name,
            payment.unit.name,
            payment.amount_paid,
            payment.payment_method,
            payment.payment_date,
            payment.month,
            payment.year,
            payment.payment_type
        ]) 