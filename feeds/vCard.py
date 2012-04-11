import vobject

def vcard(request, person) :
    v = vobject.vCard()
    v. add('n')
    v. n. value = vobject.vcard.Name(family=person.lastname, given=person.lastname)
    v. add('email')
    v. email. value = person. email
    output = v. serialize()
    filename = "%s%s. vcf" % (person. firstname, person.lastname)
    response = HttpResponse(output, mimetype="text/x-vCard")
    response['ontent-Disposition'] = 'attachment; filename=%s' % filename
    return response