get_urls_query = '''SELECT
  ci.url
FROM crl_info ci
WHERE ci.archive = 0
AND ci.subjKeyId = "%s"
UNION
SELECT
  aci.crlUrl
FROM accredited_cert_info aci
WHERE aci.archive = 0
AND aci.subjKeyId = "%s"
;'''
