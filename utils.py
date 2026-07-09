def format_time(seconds: float) -> str:
    s=int(seconds)
    h=s//3600
    m=(s%3600)//60
    s=s%60
    return f"{h:02}:{m:02}:{s:02}"

def format_pace(seconds: float)->str:
    if seconds<=0:
        return "--:--"
    m=int(seconds)//60
    s=int(seconds)%60
    return f"{m}:{s:02}"
