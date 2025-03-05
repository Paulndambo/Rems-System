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