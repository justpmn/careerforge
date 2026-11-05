
import base64
import io

import qrcode


def build_totp_qr_data_url(provisioning_uri: str) -> str:
    if (
        not provisioning_uri.startswith("otpauth://totp/")
        or len(provisioning_uri) > 2048
    ):
        raise ValueError("Invalid TOTP provisioning URI.")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
