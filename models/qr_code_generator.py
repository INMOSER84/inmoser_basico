from odoo import models, fields, api
import base64
import io
import qrcode

class QRCodeGenerator(models.AbstractModel):
    _name = 'qr.code.generator'
    _description = 'QR Code Generator'
    
    qr_code = fields.Binary(string='QR Code', compute='_generate_qr_code')
    
    def _generate_qr_code(self):
        for record in self:
            qr_data = self._get_qr_data(record)
            if qr_data:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue())
                
                record.qr_code = img_str
    
    def _get_qr_data(self, record):
        """Override this method to provide QR data for specific models"""
        return None
