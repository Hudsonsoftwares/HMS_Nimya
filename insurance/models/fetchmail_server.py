# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    imap_search_criteria = fields.Char(
        string='IMAP Search Criteria',
        default='(UNSEEN)',
        help="IMAP search criteria. Default is '(UNSEEN)'. E.g. to filter by sender: (UNSEEN FROM \"odootest998@gmail.com\")"
    )
    imap_folder = fields.Char(
        string='IMAP Folder',
        default='INBOX',
        help="IMAP folder/mailbox to select. Default is 'INBOX'."
    )

    def connect(self, allow_archived=False):
        connection = super(FetchmailServer, self).connect(allow_archived=allow_archived)
        if self.server_type == 'imap':
            # Dynamic override of search and select methods on the IMAP connection object
            original_search = getattr(connection, 'search', None)
            if original_search:
                def custom_search(charset, *criteria):
                    # If standard Odoo fetch is calling search with '(UNSEEN)'
                    if criteria == ('(UNSEEN)',) and self.imap_search_criteria:
                        _logger.info("Overriding IMAP search criteria from (UNSEEN) to %s", self.imap_search_criteria)
                        criteria = (self.imap_search_criteria,)
                    return original_search(charset, *criteria)
                # Assign the custom search method back to the connection object
                connection.search = custom_search

            original_select = getattr(connection, 'select', None)
            if original_select:
                def custom_select(mailbox='INBOX', readonly=False):
                    # If standard Odoo fetch is calling select() without argument or with 'INBOX'
                    target_mailbox = self.imap_folder or mailbox
                    _logger.info("Overriding IMAP mailbox select from %s to %s", mailbox, target_mailbox)
                    return original_select(mailbox=target_mailbox, readonly=readonly)
                connection.select = custom_select

        return connection
