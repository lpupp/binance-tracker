"""Create signals to be imported by the trading bot.

Example signal is provided.
"""

def eg_condition(df, x=['ema_25'], t=20):
    """If list of indicators is below threshold

    if x=['a', 'b'] and t = 20
    a  b
    25 40
    20 25
    5  10 <-- signal
    10 10 <-- signal
    25 10
    """

    if not isinstance(x, list):
        x = [x]

    df = df.tail(1)
    out = True
    for i in x:
        out = out and (df[i].values < t)
    return out
