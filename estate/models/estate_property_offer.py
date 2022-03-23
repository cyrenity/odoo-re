# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta

from odoo.exceptions import UserError, ValidationError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Realestate Property Offer"
    _order = "price desc"
    
    price = fields.Float('Offer Amount', required=True)
    
    state = fields.Selection(
        string='Offer Status',
        selection=[('accepted', 'Accepted'), ('refused', 'Refused')],
        help="Select status")
    
    partner_id = fields.Many2one("res.partner", string="Partner", copy=False)
    property_id = fields.Many2one("estate.property", string="Property")
    validity = fields.Integer("Offer Validity", default=7)
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_inverse_date_deadline")
    
    _sql_constraints = [
        ('check_offer_price', 'CHECK(price > 0)', 'The offer price must a positive number.'),
    ]
        
        
        
    @api.model
    def create(self, vals):
        max_offer = self.env['estate.property.offer'].search([('property_id','=', vals['property_id'])], order='price desc', limit=1)
        
        if int(vals['price']) <= int(max_offer['price']):
            raise ValidationError("The offer [%d] should be higher than [%d]" % (int(vals['price']), int(max_offer['price'])))
        
        # Set parent state
        self.env['estate.property'].browse(vals['property_id']).state = 'offer_received'
        
        return super().create(vals)
    
    
        
    @api.constrains('price')
    def _check_offer_price(self):
        for record in self:
            if (100 * float(record.price)/float(record.property_id.expected_price)) < 90:
                raise ValidationError("The offer price should be atleast 90% of the expected price.")

    
    @api.depends("validity")
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.date_deadline:
                record.validity = (record.date_deadline - record.create_date.date()).days
                
    
    # ---------------------------------------- Action Methods -------------------------------------
    def action_accept(self):
        if "accepted" in self.mapped("property_id.offer_ids.state"):
            raise UserError("An offer has already been accepted.")
        self.write(
            {
                "state": "accepted",
            }
        )
        return self.mapped("property_id").write(
            {
                "state": "offer_accepted",
                "selling_price": self.price,
                "buyer": self.partner_id.id,
            }
        )

    def action_refuse(self):
        return self.write(
            {
                "state": "refused",
            }
        )