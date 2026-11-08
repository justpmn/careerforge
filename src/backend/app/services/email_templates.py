
from html import escape


def render_email(
    title: str,
    greeting: str,
    paragraphs: list[str],
    button_label: str = "",
    button_url: str = "",
    include_logo: bool = False,
) -> str:
    logo = (
        '<img src="cid:careerforge-logo" alt="CareerForge" '
        'width="48" height="48" style="display:block;object-fit:contain;">'
        if include_logo else
        '<span style="font-weight:800;font-size:22px;color:#00c7d4;">CF</span>'
    )

    body = "".join(
        f'<p style="margin:0 0 18px;line-height:1.75;color:#475569;">'
        f'{escape(paragraph)}</p>'
        for paragraph in paragraphs
    )

    button = ""
    if button_label and button_url:
        button = (
            '<div style="margin:30px 0;">'
            f'<a href="{escape(button_url, quote=True)}" '
            'style="display:inline-block;background:#12333f;'
            'color:#ffffff;padding:15px 26px;border-radius:9px;'
            'text-decoration:none;font-weight:700;">'
            f'{escape(button_label)}</a></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:32px 12px;background:#f0f3f7;
font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" cellpadding="0" cellspacing="0"
style="width:100%;max-width:580px;margin:auto;background:#ffffff;
border-radius:14px;border:1px solid #e2e8f0;">
<tr><td style="height:5px;background:#00c7d4;"></td></tr>
<tr><td style="padding:36px 38px 14px;">
<table role="presentation"><tr>
<td style="padding-right:14px;">{logo}</td>
<td>
<strong style="font-size:23px;color:#111827;">CareerForge</strong>
<div style="font-size:10px;color:#64748b;letter-spacing:2px;
margin-top:5px;">YOUR NEXT MOVE, MADE CLEARER</div>
</td>
</tr></table>
</td></tr>
<tr><td style="padding:20px 38px 36px;">
<h1 style="font-size:28px;line-height:1.2;color:#111827;
margin:0 0 22px;">{escape(title)}</h1>
<p style="font-size:16px;font-weight:600;color:#111827;">
{escape(greeting)}</p>
{body}
{button}
<p style="font-size:14px;color:#64748b;margin-top:28px;">
The CareerForge Team</p>
</td></tr>
<tr><td style="background:#f8fafc;padding:20px 38px;
border-top:1px solid #e2e8f0;">
<p style="margin:0;font-size:12px;color:#94a3b8;">
CareerForge · Make your next move count.
</p>
</td></tr>
</table>
</body>
</html>"""
