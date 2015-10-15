import json
import socket
import re
from trac.core import *
from trac.config import Option, IntOption
from trac.ticket.api import ITicketChangeListener
# from trac.versioncontrol.api import IRepositoryChangeListener
from trac.wiki.api import IWikiChangeListener
import unicodedata


def prepare_ticket_values(ticket, action=None):
    values = ticket.values.copy()
    values['id'] = "#" + str(ticket.id)
    values['action'] = action
    values['url'] = ticket.env.abs_href.ticket(ticket.id)
    values['project'] = ticket.env.project_name.encode('utf-8').strip()
    values['env'] = ticket.env.config.get('rpc-out','source')

    if values['description'].__class__.__name__ == "unicode":
        values['description'] = unicodedata.normalize('NFKD', values['description']).encode('ascii', 'ignore')

    return values


class IrkerNotifcationPlugin(Component):
    implements(ITicketChangeListener, IWikiChangeListener)
    host = Option('irker', 'host', 'localhost',
                  doc="Host on which the irker daemon resides.")
    port = IntOption('irker', 'port', 6659,
                     doc="Irker listen port.")
    target = Option('irker', 'target', 'irc://localhost/#commits',
                    doc="IRC channel URL to which notifications are to be sent.")

    def notify(self, message):
        data = {"to": self.target, "privmsg": message.encode('utf-8').strip()}
        try:
            s = socket.create_connection((self.host, self.port))
            s.sendall(json.dumps(data))
        except socket.error:
            return False
        return True

    def ticket_created(self, ticket):
        values = prepare_ticket_values(ticket, 'created')
        values['author'] = values['reporter']
        values['type'] = 'ticket'
        values['author'] = re.sub(r' <.*', '', values['author'])

        message = "\u0002[ticket:{}] \u001F{}\u001F {}\u0002 (reported by {}, assigned to {}) <{}> {}".format(
            values['env'],
            values['id'],
            values['summary'],
            values['author'],
            values['owner'],
            ticket.env.config.get('rpc-out', 'base_url') + "ticket/" + str(ticket.id),
            ' / '.join([line.strip() for line in values['description'].split('\n') if line and line.strip()])
        )

        self.notify(message)

    def ticket_changed(self, ticket, comment, author, old_values):
        action = 'changed'
        if 'status' in old_values:
            if 'status' in ticket.values:
                if ticket.values['status'] != old_values['status']:
                    action = ticket.values['status']
        values = prepare_ticket_values(ticket, action)
        values.update({
            'comment': comment or '',
            'author': author or '',
            'old_values': old_values
        })

        comment_out = unicodedata.normalize('NFKD', comment).encode('ascii', 'ignore') if comment.__class__.__name__ == "unicode" else comment

        message = "\u0002[ticket:{}] \u001F{}\u001F {} (\u001F{}\u001F)\u0002 <{}> {}: {}".format(
            values['env'],
            values['id'],
            values['summary'],
            values['action'],
            ticket.env.config.get('rpc-out', 'base_url') + "ticket/" + str(ticket.id),
            ' / '.join([line.strip() for line in comment_out.split('\n') if line and line.strip()])
        )

        self.notify(message)

    def ticket_deleted(self, ticket):
        pass

    def wiki_page_added(self, page):

        history = page.get_history()[-1]
        author = history[2] if history[2] else ""
        comment = history[3] if history[3] else ""

        env = page.env.config.get('rpc-out','source')

        comment_out = "<no comment>"
        if (not (comment is None)) and comment != '':
            if comment.__class__.__name__ == "unicode":
                comment_out = unicodedata.normalize('NFKD', comment).encode('ascii','ignore')
            else:
                comment_out = comment


        message = "\u0002[wiki:{}] \u001F{}\u001F\u0002 (created by {}) <{}> {}".format(
            env,
            page.name,
            author,
            page.env.config.get('rpc-out','base_url')+"wiki/"+page.name,
            ' / '.join([line.strip() for line in comment_out.split('\n') if line and line.strip()])
        )

        self.notify(message)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):

        env = page.env.config.get('rpc-out','source')

        if comment.__class__.__name__ == "unicode":
            comment_out = unicodedata.normalize('NFKD', comment).encode('ascii','ignore')
        else:
            comment_out = comment

        message = "\u0002[wiki:{}] \u001F{}\u001F\u0002 (edited by {}) <{}> {}".format(
            env,
            page.name,
            author,
            page.env.config.get('rpc-out','base_url')+"wiki/"+page.name,
            ' / '.join([line.strip() for line in comment_out.split('\n') if line and line.strip()])
        )

        self.notify(message)

    def wiki_page_deleted(self, page):
        pass

    def wiki_page_version_deleted(self, page):
        pass

