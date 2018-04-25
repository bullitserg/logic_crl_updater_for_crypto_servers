get_urls_query = '''SELECT
  DISTINCT ci.url
FROM crl_info ci
WHERE ci.archive = 0
AND ci.subjKeyID = "%s"
;'''