#!/bin/sh

subj="/C=US/ST=CA/L=SF/O=Corp/OU=Dept/CN=localhost"

for i in one two; do
    openssl req -new -nodes -days 3650 -x509 -keyout ${i}_ca.key \
        -out ${i}_ca.cert -subj ${subj}_ca

    for n in server client; do
        f="${i}_${n}"
        openssl req -new -nodes -keyout ${f}.key -out ${f}.csr -subj $subj
        openssl x509 -req -CA ${i}_ca.cert -CAkey ${i}_ca.key -CAcreateserial \
            -days 3650 -trustout -addtrust ${n}Auth -in ${f}.csr -out ${f}.cert 
        rm ${f}.csr
    done
done

rm *.srl
    
