from enum import Enum

class MonthsNames(Enum):
    JANUARY = 'January'
    FEBRUARY = 'February'
    MARCH = 'March'
    APRIL = 'April'
    MAY = 'May'
    JUNE = 'June'
    JULY = 'July'
    AUGUST = 'August'
    SEPTEMBER = 'September'
    OCTOBER = 'October'
    NOVEMBER = 'November'
    DECEMBER = 'December'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

class Months(Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


MONTHS_LIST = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
]

years = [
    2024,
    2025,
    2026,
    2027,
    2028,
    2029,
    2030,
    2031,
    2032,
    2033,
    2034,
    2035,
    2036,
    2037,
    2038,
    2039,
    2040
]

YEARS_LIST = [str(x) for x in years]

LEASE_DURATIONS = [
    '3 Months',
    '6 Months',
    '9 Months',
    '1 Year',
    '2 Years',
    '3 Years',
    '4 Years'
]

UNIT_TYPES = [
    'Single Room',
    'Bedsitter',
    'Studio',
    '1 Bedroom',
    '2 Bedroom',
    '3 Bedroom',
    '4 Bedroom'
]

UNIT_STATUSES = [
    'Vacant',
    'Occupied',
    'Under Maintenance'
]

PAYMENT_STATUSES = [
    'Future',
    'Pending',
    'Paid',
    'Overdue',
    'Partially Paid'
]

class PaymentStatuses(Enum):
    FUTURE = 'Future'
    PENDING = 'Pending'
    PAID = 'Paid'
    OVERDUE = 'Overdue'
    PARTIALLY_PAID = 'Partially Paid'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]