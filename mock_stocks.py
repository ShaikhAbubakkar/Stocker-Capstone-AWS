# Mock stock data for testing
# In production, replace with real API (Alpha Vantage, IEX Cloud, etc.)

MOCK_STOCKS = {
    'AAPL': {
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'price': 178.42,
        'open': 175.18,
        'high': 179.52,
        'low': 174.85,
        'volume': '52.4M',
        'market_cap': '$2.78T',
        'pe_ratio': 29.45,
        'change': 3.24,
        'change_percent': 1.85
    },
    'GOOGL': {
        'symbol': 'GOOGL',
        'name': 'Alphabet Inc.',
        'price': 142.58,
        'open': 140.25,
        'high': 144.12,
        'low': 139.85,
        'volume': '22.5M',
        'market_cap': '$1.42T',
        'pe_ratio': 25.13,
        'change': 2.33,
        'change_percent': 1.66
    },
    'MSFT': {
        'symbol': 'MSFT',
        'name': 'Microsoft Corporation',
        'price': 415.23,
        'open': 412.50,
        'high': 418.75,
        'low': 411.20,
        'volume': '18.9M',
        'market_cap': '$3.08T',
        'pe_ratio': 32.85,
        'change': 2.73,
        'change_percent': 0.66
    },
    'AMZN': {
        'symbol': 'AMZN',
        'name': 'Amazon.com Inc.',
        'price': 195.84,
        'open': 193.45,
        'high': 197.62,
        'low': 192.80,
        'volume': '38.2M',
        'market_cap': '$2.05T',
        'pe_ratio': 56.32,
        'change': 2.39,
        'change_percent': 1.23
    },
    'TSLA': {
        'symbol': 'TSLA',
        'name': 'Tesla Inc.',
        'price': 248.75,
        'open': 245.20,
        'high': 251.50,
        'low': 244.15,
        'volume': '125.6M',
        'market_cap': '$785.5B',
        'pe_ratio': 68.42,
        'change': 3.55,
        'change_percent': 1.45
    },
    'META': {
        'symbol': 'META',
        'name': 'Meta Platforms Inc.',
        'price': 524.32,
        'open': 520.15,
        'high': 528.95,
        'low': 519.50,
        'volume': '12.3M',
        'market_cap': '$1.65T',
        'pe_ratio': 28.56,
        'change': 4.17,
        'change_percent': 0.80
    },
    'NVDA': {
        'symbol': 'NVDA',
        'name': 'NVIDIA Corporation',
        'price': 875.43,
        'open': 868.50,
        'high': 882.75,
        'low': 865.20,
        'volume': '35.4M',
        'market_cap': '$2.15T',
        'pe_ratio': 65.23,
        'change': 6.93,
        'change_percent': 0.80
    },
    'NFLX': {
        'symbol': 'NFLX',
        'name': 'Netflix Inc.',
        'price': 287.65,
        'open': 284.20,
        'high': 291.50,
        'low': 283.85,
        'volume': '3.2M',
        'market_cap': '$127.3B',
        'pe_ratio': 38.42,
        'change': 3.45,
        'change_percent': 1.22
    }
}


def get_stock(symbol):
    """Get stock data by symbol"""
    return MOCK_STOCKS.get(symbol.upper())


def search_stocks(query):
    """Search stocks by symbol or name"""
    query = query.upper()
    results = []
    
    for symbol, data in MOCK_STOCKS.items():
        if query in symbol or query in data['name'].upper():
            results.append(data)
    
    return results


def get_all_stocks():
    """Get all available stocks"""
    return list(MOCK_STOCKS.values())
