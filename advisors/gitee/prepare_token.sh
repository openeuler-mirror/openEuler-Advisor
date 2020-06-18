#!/bin/bash

# refer to gitee.com/api/v5/oauth_doc#/list-item-2
source ~/.gitee_secret
echo "Refreshing ~/.gitee_token.json"
curl -s -X POST --data-urlencode "grant_type=password" --data-urlencode "username=$username" --data-urlencode "password=$password" --data-urlencode "client_id=$client_id" --data-urlencode "client_secret=$client_secret" --data-urlencode "scope=projects issues" https://gitee.com/oauth/token > ~/.gitee_token.json
chmod 400 ~/.gitee_token.json
