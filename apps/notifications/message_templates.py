def format_water_bill_message(tenant_name: str, amount: float) -> str:
    return f"""
Hello *{tenant_name}*,

Your water bill payment of *{amount}* has been received and recorded. 

Thank you.
"""


def format_rent_bill_message(tenant_name: str, amount: float) -> str:
    return f"""
Hello *{tenant_name}*,

Your rent bill payment of *{amount}* has been received and recorded. 

Thank you.
"""


def format_garbage_bill_message(tenant_name: str, amount: float) -> str:
    return f"""
Hello *{tenant_name}*,

Your garbage bill payment of *{amount}* has been received and recorded. 

Thank you.
"""


def format_unit_bill_message(tenant_name: str, month: str, year: str) -> str:
    return f"""
Hello *{tenant_name}*,

We would like to inform you that your monthly bill for *{month}, {year}* has been fully paid. 

Thank you.
"""


def format_bill_payment_message(
    tenant_name: str, rent_amount, garbage_amount, water_amount
) -> str:
    return f"""
Hello *{tenant_name}*,

We would like to inform you that your payment has been successfully recorded. 
Here are the details of your payment:
- Rent Amount: *{rent_amount}*
- Garbage Amount: *{garbage_amount}*
- Water Amount: *{water_amount}*
- Total Amount: *{rent_amount + garbage_amount + water_amount}*
Your payment has been successfully recorded and your account has been updated accordingly.
If you have any questions or concerns, please feel free to reach out to us.
We appreciate your prompt payment and look forward to serving you in the future.
Thank you.
"""
