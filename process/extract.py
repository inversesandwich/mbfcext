import json
import os
import csv

from unidecode import unidecode

from Source import Source
from Source import db


def get_domains(where, label):
    global table_hosts
    domains = []
    for source in Source.select().where(where).order_by(Source.MozRankURL.desc()):
        domains.append(source.domain)
        host = source.domain
        if host not in table_hosts:
            table_hosts[host] = {
                "url": source.homepage,
                "labels": [],
                "name": source.name
            }
        if label != "factual-reporting":
            table_hosts[host]["labels"].append(label)
    return sorted(set(domains))


def add_sources(key, title, domains):
    return {
        "key": key,
        "href": "#/home/" + key,
        "name": title,
        "gcse": "",
    }


def add_hosts(label, hosts):
    global tsv_hosts, max_labels,sources
    for host in hosts:
        if not host in tsv_hosts:
            tsv_hosts[host] = {
                "url": host + "/*",
                "labels": ["_cse_i0l4anspnui"],
                "domain": host,
            }
        tsv_hosts[host]["labels"].append(label)
        max_labels = max(max_labels, len(tsv_hosts[host]["labels"]))


def add_facet(label, name):
    global facets
    facets += """      <FacetItem>
        <Label name="%s" mode="FILTER" enable_for_facet_search="false">
          <Rewrite></Rewrite>
        </Label>
        <Title>%s</Title>
      </FacetItem>
""" % (label, name)


csources = {}
sources = {}
sources_all = {}
sources_error = {}
sources_review = {}

facets = ""
tsv_hosts = {}
table_hosts = {}
max_labels = 1

skeys = ["name", "bias", "facebook_url", "homepage", "url", "reporting", "Links", "MozRankURL", "Popularity"]

db.execute_sql("UPDATE `source` INNER JOIN ( SELECT id, domain, url, ExternalEquityLinks, ROUND(100 * ((SELECT COUNT(*) FROM `source` as s2 WHERE s2.ExternalEquityLinks < `source`.`ExternalEquityLinks`))/(SELECT COUNT(*) FROM `source`), 0) AS Popularity FROM `source`) AS t ON `source`.id=t.id SET `source`.Popularity = t.Popularity")

for source in Source.select().where((Source.complete == 1) & (Source.review == 0)):
    item = source.toJSON()
    for k in item:
        try:
            item[k] = unidecode(item[k])
        except AttributeError:
            pass
        except UnicodeDecodeError:
            pass
    try:
        complete = item['domain'] != None and item['homepage'] != None
        if not complete and item['complete']:
            print('Flagging item for review: ', item['url'])
            source.review = True
            source.save()
        if item['complete']:
            item['review'] = False
            item['error'] = False
        if item['domain'] == None or item['domain'] == 'null':
            item['review'] = True
        else:
            item['review'] = False
        if not item['review']:
            if item['bias'] == 'fake-news':
                item['reporting'] = 'FAKE'
            item['domain'] = item['domain'].replace("www.", "")

    except AttributeError:
        # if item['url'].find('mediabiasfactcheck.com/msnbc/') > -1:
        #     print(repr(item))
        pass
    except TypeError:
        # if item['url'].find('mediabiasfactcheck.com/msnbc/') > -1:
        #     print(repr(item))
        continue
    try:
        key = item['domain'] if item['domain'] else item['url']
        sources_all[key] = item
        if not item['error'] and not item['review']:
            sources[key] = {k: item[k] for k in skeys}
            sources[key]['domain'] = key
            csources[key] = {k[:1]: item[k] for k in skeys}
            csources[key]['d'] = key
        if item['error']:
            sources_error[key] = item
        if item['review']:
            sources_review[key] = item
    except KeyError:
        print(repr(item))
    except TypeError:
        # if item['url'].find('mediabiasfactcheck.com/msnbc/') > -1:
        #     print(repr(item))
        continue

if "mediabiasfactcheck.com" not in sources:
    sources_all["mediabiasfactcheck.com"] = {
        "DomainAuthority": 45.9069,
        "ExternalEquityLinks": 11496,
        "HTTPStatusCode": 301,
        "Links": 1,
        "MozRankURL": 5.32185,
        "MozRankURLRaw": 1.60866e-10,
        "Timelastcrawled": 1505684836,
        "bias": "center",
        "complete": True,
        "crawled_at": False,
        "details": "",
        "domain": "mediabiasfactcheck.com",
        "domains": "",
        "error": False,
        "facebook_url": "https://www.facebook.com/mediabiasfactcheck/",
        "homepage": "http://mediabiasfactcheck.com/",
        "name": "Media Bias/Fact Check",
        "notes": "",
        "ranked": True,
        "raw": "",
        "reporting": "VERY HIGH",
        "review": True,
        "review_details": "",
        "text": "",
        "updated_at": False,
        "url": "http://mediabiasfactcheck.com/independent-journal-review/"
    }
    
todo = {
    "sources-all.json":    sources_all,
    "sources.json":        sources,
    "csources.json":       csources,
    "sources-error.json":  sources_error,
    "sources-review.json": sources_review,
}
for k in todo:
    v = todo[k]
    try:
        if k == "sources.json" or k == "csources.json":
            s = json.dumps(v, encoding='latin1')
        else:
            s = json.dumps(v, encoding='latin1', sort_keys=True, indent=4, separators=(',', ': '))
    except UnicodeDecodeError as ude:
        pass
    open(k, "w").write(s)
    print('Saved %d items to %s' % (len(v.keys()), k))
    if k == "csources.json":
        if len(v.keys()) > 1700:
            open("valid.export", "w").write("\n")
        else:
            if os.path.exists("valid.export"):
                os.unlink("valid.export")

sources = {}
hosts = {}
baseline = ((Source.complete == 1) & (Source.review == 0) & (Source.reporting << ['HIGH', 'VERY HIGH']) & (Source.Links > 1000))

domains = get_domains(baseline, "factual-reporting")
sources["factual-reporting"] = add_sources("factual-reporting", "News Sources with Highly Factual Reporting (all biases)", domains)
hosts["factual-reporting"] = domains

domains = get_domains(baseline & (Source.bias << ['left-center', 'right-center', 'center']), "mostly-center")
sources["mostly-center"] = add_sources("mostly-center", "Left-Center, Least and Right-Center Biased Sources with Highly Factual Reporting", domains)
hosts["mostly-center"] = domains
add_facet("mostly-center", "Mostly Center")
add_hosts("mostly-center", domains)

domains = get_domains(baseline & (Source.bias << ['left', 'left-center']), "left-leaning")
sources["left-leaning"] = add_sources("left-leaning", "Left, Left-Center and Least Biased Sources with Highly Factual Reporting", domains)
hosts["left-leaning"] = domains
add_facet("left-leaning", "Left Leaning")
add_hosts("left-leaning", domains)

domains = get_domains(baseline & (Source.bias << ['right', 'right-center']), "right-leaning")
sources["right-leaning"] = add_sources("right-leaning", "Right, Right-Center and Least Biased Sources with Highly Factual Reporting", domains)
hosts["right-leaning"] = domains
add_facet("right-leaning", "Right Leaning")
add_hosts("right-leaning", domains)

biases = json.load(open("biases.json", "r"))
for bias in biases:
    if bias == 'fake-news' or bias == 'satire' or bias == 'conspiracy':
        continue
    domains = get_domains(baseline & (Source.bias == bias), bias + "-only")
    sources[bias + "-only"] = add_sources(bias + "-only", biases[bias]["name"] + " Sources only with Highly Factual Reporting", domains)
    hosts[bias + "-only"] = domains
    add_facet(bias + "-only", biases[bias]["name"].replace(" Bias", ""))
    add_hosts(bias + "-only", domains)

js = []
for key in sorted(table_hosts.keys()):
    js.append(table_hosts[key])
open("GCS/hosts.json", "w").write(json.dumps(js, encoding='latin1'))

open("GCS/labels.xml","w").write("\n    <Facet>\n%s\n    </Facet>" % facets)
with open("GCS/annotations.tsv", "w") as fp:
    writer = csv.writer(fp, delimiter='\t')
    writer.writerow(["URL"] + ['Label'] * max_labels + ['Score'])
    for key in tsv_hosts:
        host = tsv_hosts[key]
        writer.writerow([host["url"]] + host["labels"])

