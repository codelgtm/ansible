#!/bin/python
#
# Script to get simple usage data for ANS subscriptions
#
import optparse
import urlparse
import urllib
import csv
import json
import logging
from datetime import datetime

def main():
    """Process command line and get usage

    """
    options = process_options()

    set_logging(options)

    subscriptions = get_subscriptions(options)

    policy_counts = dict([(name, get_policy_counts(options, name))
                          for name in subscriptions])

    user_counts = dict([(name, get_user_counts(options, name))
                        for name in subscriptions])

    save_results(options, subscriptions, policy_counts, user_counts)

    if options.policies:
        for name in subscriptions:
            get_policies(options, name)

def process_options():
    """Process command line and return options object

    """
    parser = optparse.OptionParser(usage='%prog [options] ACCOUNT PASSWORD')

    define_options(parser)
    options, arguments = parser.parse_args()
    check_options(parser, options, arguments)

    return options

def define_options(parser):
    """Define options for the cli parser

    """
    parser.add_option('--ung', dest='ung',
                      help='User and groups url, with credentials', metavar='URL')

    parser.add_option('--policies', dest='policies', metavar='DIRECTORY',
                      help='Get list of policies for subscriptions and stores in directory')

    parser.add_option('--output', dest='output',
                      help='Output csv file (default substats.csv)')
    parser.set_defaults(output='substats.csv')

    parser.add_option('--debug', action='store_const', dest='loglevel',
                      const=logging.DEBUG,
                      help='Log at debug level')
    parser.set_defaults(loglevel=logging.INFO)


def check_options(parser, options, arguments):
    """Check and refine options

    """
    if len(arguments) != 2:
        parser.error('Need Cloudant account and password')

    options.account = arguments[0]
    options.password = arguments[1]

    if options.ung:
        o = urlparse.urlparse(options.ung)
        if (o.scheme != 'https' or not o.hostname or not o.username or not o.password):
            parser.error('Users and groups URL must include credentials (https://user:passsword@host.com)')


def set_logging(options):
    logging.basicConfig(level=options.loglevel)


def get_subscriptions(options):
    """Get subscription names from the common database

    """
    logger = logging.getLogger('subscriptions')
    logger.debug('Getting subscription list')

    result = cloudant_read(options, '/common/_design/all/_view/byDocType',
                            {'startkey': '"Subscription"', 'endkey': '"Subscription "',
                             'include_docs': 'true'})

    return dict([(row['doc']['SubscriptionID'],
                  {'offering':row['doc'].get('SubscriptionSource'),
                   'start':formatms(row['doc'].get('StartDate', 0)),
                   'bss':row['doc'].get('BSSSubscriptionID'),
                   'state':row['doc'].get('State'),
                   'tenant':row['doc'].get('TenantID'),
                   'space':row['doc'].get('SpaceID'),
                   'plan':row['doc'].get('PlanID')})
                 for row in result['rows']])

def get_policy_counts(options, subscription):
    """Get the policy counts for the subscription

    returns (enabled, disabled)

    """
    logger = logging.getLogger('policy')
    logger.debug('Getting policy list for %s', subscription)

    result = cloudant_read(options,
                           '/an%s/_design/all/_view/byDocType' % (urllib.quote(subscription.lower()),),
                            {'startkey': '"EventFilter"', 'endkey': '"EventFilter "',
                             'include_docs': 'true'})

    if result.get('rows'):
        enabled = len([row
                       for row in result['rows']
                       if row['doc']['Enabled']])

        return (enabled, len(result['rows']) - enabled)
    else:
        return (-1, -1)

def get_policies(options, subscription):
    """Get policy definitions for the given subscription and stores in given directory
    """
    logger = logging.getLogger('policies')
    logger.debug('Getting policies for %s', subscription)

    result = cloudant_read(options,
                           '/an%s/_design/all/_view/byDocType' % (urllib.quote(subscription.lower()),),
                            {'startkey': '"EventFilter"', 'endkey': '"EventFilter "',
                             'include_docs': 'true'})
    if result.get('rows'):
        with open('%s/%s' % (options.policies, subscription.lower()), 'w') as outfile:
            json.dump(result.get('rows'), outfile, sort_keys=True, indent=4, separators=(',', ': '))

def get_user_counts(options, subscription):
    """Get user count for the given subscription

    Returns empty dictionary if Users and Groups URL is not given

    """
    if not options.ung:
        return {}

    logger = logging.getLogger('users')
    logger.debug('Getting user list for %s', subscription)

    url = urlparse.urljoin(options.ung,
                           '/clops/user/request/subscription/%s/user/*' % (urllib.quote(subscription),))
    result = json_read(url)

    if result.get('rows'):
        return len(result['rows'])
    else:
        return -1


def cloudant_read(options, path, query=None):
    """Read from Cloudant

    """
    url = urlparse.urlunparse(['https',
                               '%s:%s@%s.cloudant.com' % (options.account, options.password, options.account),
                               path,
                               None,
                               query and urllib.urlencode(query),
                               None])
    return json_read(url)

def json_read(url):
    """Read JSON from the given url

    """
    handle = urllib.urlopen(url)
    data = handle.read()
    handle.close()

    return json.loads(data)

def save_results(options, subscriptions, policy_counts, user_counts):
    """Write results to CSV file

    """
#   columns = ['subsciption', 'tenant', 'space', 'plan', 'bss', 'start',
#              'offering', 'state', 'enabled policies', 'disabled policies',
#              'users']
    columns = ['subsciption', 
               'enabled policies', 'disabled policies',
               'users']

    rows = [(str(name),
#            subscriptions[name]['tenant'],
#            subscriptions[name]['space'],
#            subscriptions[name]['plan'],
#            subscriptions[name]['bss'],
#            subscriptions[name]['start'],
#            subscriptions[name]['offering'],
#            subscriptions[name]['state'],
             policy_counts.get(name, [-1, -2])[0],
             policy_counts.get(name, [-1, -2])[1],
             user_counts.get(name, -2))
            for name in subscriptions]

    with open(options.output, 'w') as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)

def formatms(ms):
    """Format Javascript time, miliseconds since UNIX epoch

    """
    return datetime.utcfromtimestamp(ms/1000).isoformat() + 'Z'

#
# Process command line 

main()
