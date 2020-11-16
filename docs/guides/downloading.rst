.. _downloading:

Downloading Legislation
=======================================

Legislice is a utility for downloading the text of statutes and
constitutional provisions, and then creating computable objects
representing passages from those provisions. This guide will show
how to get started.

Legislice depends on the `AuthoritySpoke
API <https://authorityspoke.com/>`__ as its source of legislative text.
Currently the API serves the text of the United States Constitution,
plus versions of the United States Code in effect since 2013. Provisions
of the United States Code that were repealed prior to 2013 aren’t yet
available through the API, and neither are any regulations or any state
law.

.. _using-an-api-token:

Using an API token
---------------------

To get started, `make an account on
authorityspoke.com <https://authorityspoke.com/account/signup/>`__. Then
go to the `User Profile
page <https://authorityspoke.com/account/profile/>`__, where you can
find your API token. The token is a 40-character string of random
letters and numbers. You’ll be sending this token to AuthoritySpoke to
validate each API request, and you should keep it secret as you would a
password.

There are several ways for Python to access your API token. One way
would be to simply define it as a Python string, like this:

.. code:: ipython3

    TOKEN = "YOU_COULD_PUT_YOUR_API_TOKEN_HERE"

However, a better option is to make your API token an **environment
variable**, and then use Python to access that variable. Using a Python
library called `dotenv <https://pypi.org/project/python-dotenv/>`__, you
can define an environment variable in a file called ``.env`` in the root
of your project directory. For instance, the contents of the file
``.env`` could look like this:

   LEGISLICE_API_TOKEN=YOUR_API_TOKEN_GOES_HERE

By doing this, you can avoid having a copy of your API token in your
Python working file or notebook. That makes it easier to avoid
accidentally publishing the API token or sharing it with unauthorized
people.

Here’s an example of loading an API token from a ``.env`` file using
``dotenv``.

.. code:: ipython3

    import os
    from dotenv import load_dotenv
    load_dotenv()

    TOKEN = os.getenv("LEGISLICE_API_TOKEN")

Now you can use the API token to create a Legislice :class:`~legislice.download.Client` object.
This object holds your API token, so you can reuse the :class:`~legislice.download.Client`
without re-entering your API token repeatedly.

.. code:: ipython3

    from legislice.download import Client
    client = Client(api_token=TOKEN)

.. _fetching-a-provision:

Fetching a provision from the API
------------------------------------

To download legislation using the :class:`~legislice.download.Client`, we must specify a
``path`` to the provision we want, and optionally we can specify the
``date`` of the version of the provision we want. If we don’t specify
a date, we’ll be given the most recent version of the provision.

The ``path`` citation format is based on the section identifiers in the
`United States Legislative Markup
standard <https://uscode.house.gov/download/resources/USLM-User-Guide.pdf>`__,
which is a United States government standard used by the Office of the
Law Revision Counsel for publishing the United States Code. Similar to a
URL path in a web address, the ``path`` format is a series of labels
connected with forward slashes. The first part identifies the
jurisdiction, the second part (if any) identifies the legislative code
within that jurisdiction, and so on.

If we don’t know the right citation for the provision we want, we can
sign in to an AuthoritySpoke account and
browse the `directory of available
provisions <https://authorityspoke.com/legislice/>`__, where the links
to each provision show the correct ``path`` for that provision. Or we can browse an `HTML
version of the API itself <https://authorityspoke.com/api/v1/>`__. If
the error message “Authentication credentials were not
provided” appears, that means we aren’t signed in, and we might want to go
back to the `login page <https://authorityspoke.com/account/login/>`__.

The :meth:`~legislice.download.Client.fetch` method makes an API call to AuthoritySpoke, and
returns JSON that is been converted to a Python :py:class:`dict`. There are
fields representing the ``content`` of the provision, the ``start_date``
when the provision went into effect, and more.

Here’s an example of how to fetch the text of the Fourth Amendment using
the :class:`~legislice.download.Client`.

    >>> fourth_a = client.fetch(query="/us/const/amendment/IV")
    >>> fourth_a
    {'heading': 'AMENDMENT IV.',
    'content': 'The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized.',
    'start_date': '1791-12-15',
    'node': '/us/const/amendment/IV',
    'children': [],
    'end_date': None,
    'url': 'https://authorityspoke.com/api/v1/us/const/amendment/IV/',
    'citations': [],
    'parent': 'https://authorityspoke.com/api/v1/us/const/amendment/'}

.. _loading-an-enactment:

Loading an Enactment object
------------------------------

If all we needed was to get a JSON response from the API, we could
have used a more general Python library like ``requests``. Legislice
also lets us load the JSON response as a :class:`legislice.enactments.Enactment` object, which
has methods for selecting some but not all of the provision’s
text. One way to load an :class:`~legislice.enactments.Enactment` is with the
:class:`~legislice.download.Client`'s :meth:`~legislice.download.Client.read_from_json` method.

    >>> client.read_from_json(fourth_a)
    Enactment(source=/us/const/amendment/IV, start_date=1791-12-15, selection=TextPositionSet([TextPositionSelector[0, 332)]))

Instead of always using :meth:`~legislice.download.Client.fetch` followed by
:meth:`~legislice.download.Client.read_from_json`, we can combine the two functions together
with :meth:`~legislice.download.Client.read`. In this example, we’ll use
:meth:`~legislice.download.Client.read` to load a
constitutional amendment that contains subsections, to show that the
structure of the amendment is preserved in the resulting
:class:`~legislice.enactments.Enactment` object.

.. code:: ipython3

    thirteenth_a = client.read(query="/us/const/amendment/XIII")

The string representation of this provision includes both the selected
text (which is the full text of the amendment) as well as a citation to
the provision with its effective date.

Currently the only supported citation format is the path-style citation
used in United States Legislative Markup. Future versions of Legislice
may support the ability to convert to traditional statute citation
styles.

    >>> str(thirteenth_a)
    '"Neither slavery nor involuntary servitude, except as a punishment for crime whereof the party shall have been duly convicted, shall exist within the United States, or any place subject to their jurisdiction. Congress shall have power to enforce this article by appropriate legislation." (/us/const/amendment/XIII 1865-12-18)'

The text of the Thirteenth Amendment is all within Section 1 and Section
2 of the amendment. You can use the ``Enactment.children`` property to
get a list of provisions contained within an ``Enactment``.

    >>> thirteenth_a.children
    [Enactment(source=/us/const/amendment/XIII/1, start_date=1865-12-18, selection=TextPositionSet([TextPositionSelector[0, 207)])),
    Enactment(source=/us/const/amendment/XIII/2, start_date=1865-12-18, selection=TextPositionSet([TextPositionSelector[0, 77)]))]

Then we can access each child provision as its own ``Enactment`` object
from the ``children`` list. Remember that lists in Python start at index
0, so if we want Section 2, we’ll find it at index 1 of the
``children`` list.

    >>> str(thirteenth_a.children[1])
    '"Congress shall have power to enforce this article by appropriate legislation." (/us/const/amendment/XIII/2 1865-12-18)'

.. _downloading-prior-versions-of-an-enactment:

Downloading prior versions of an Enactment
---------------------------------------------

The API can be used to access specific provisions deeply nested within
the United States Code, and also to access multiple date versions of the
same provision. Here’s a subsection of an appropriations statute as of
2015. We can use the ``end_date`` attribute to find when this version of
the statute was displaced by a new version.

    >>> old_grant_objective = client.read(query="/us/usc/t42/s300hh-31/a/1", date="2015-01-01")
    >>> old_grant_objective.content
    'strengthening epidemiologic capacity to identify and monitor the occurrence of infectious diseases and other conditions of public health importance;'

    >>> str(old_grant_objective.end_date)
    '2019-07-05'


And here’s the same provision as of 2020. Its content has changed.

    >>> new_grant_objective = client.read(query="/us/usc/t42/s300hh-31/a/1", date="2020-01-01")
    >>> new_grant_objective.content
    'strengthening epidemiologic capacity to identify and monitor the occurrence of infectious diseases, including mosquito and other vector-borne diseases, and other conditions of public health importance;'


The 2020 version of the statute has ``None`` in its ``end_date`` field
because it’s still in effect.

    >>> str(new_grant_objective.end_date)
    'None'

.. _exploring-the-structure-of-a-legislative-code:

Exploring the structure of a legislative code
------------------------------------------------

When we query the API for a provision at a path with less than four
parts (e.g., when we query for an entire Title of the United States
Code), the response doesn’t include the full text of the provision’s
children. Instead, it only contains URLs that link to the child nodes.
This might help to automate the process of navigating the API and
discovering the provisions we want. Here’s an example that discovers
the URLs for the articles of the US Constitution.

    >>> articles = client.read(query="/us/const/article")
    >>> articles.children
    ['https://authorityspoke.com/api/v1/us/const/article/I/',
     'https://authorityspoke.com/api/v1/us/const/article/II/',
     'https://authorityspoke.com/api/v1/us/const/article/III/',
     'https://authorityspoke.com/api/v1/us/const/article/IV/',
     'https://authorityspoke.com/api/v1/us/const/article/V/',
     'https://authorityspoke.com/api/v1/us/const/article/VI/',
     'https://authorityspoke.com/api/v1/us/const/article/VII/']

.. _downloading-enactments-from-cross-references:

Downloading Enactments from cross-references
-----------------------------------------------

If an :class:`~legislice.enactments.Enactment` loaded from the API references other provisions, it may
provide a list of :class:`~legislice.enactments.CrossReference` objects when we call its
:meth:`~legislice.enactments.BaseEnactment.cross_references` method. You can pass one of these
:class:`~legislice.enactments.CrossReference` objects to the
:meth:`~legislice.download.Client.fetch` or
:meth:`~legislice.download.Client.read` method of
the download client to get the referenced :class:`~legislice.enactments.Enactment`.

    >>> infringement_provision = client.read("/us/usc/t17/s109/b/4")
    >>> str(infringement_provision)
    '"Any person who distributes a phonorecord or a copy of a computer program (including any tape, disk, or other medium embodying such program) in violation of paragraph (1) is an infringer of copyright under section 501 of this title and is subject to the remedies set forth in sections 502, 503, 504, and 505. Such violation shall not be a criminal offense under section 506 or cause such person to be subject to the criminal penalties set forth in section 2319 of title 18." (/us/usc/t17/s109/b/4 2013-07-18)'

    >>> infringement_provision.cross_references()
    [CrossReference(target_uri="/us/usc/t17/s501", reference_text="section 501 of this title"),
     CrossReference(target_uri="/us/usc/t18/s2319", reference_text="section 2319 of title 18")]

    >>> reference_to_title_18 = infringement_provision.cross_references()[1]
    >>> referenced_enactment = client.read(reference_to_title_18)
    >>> str(referenced_enactment)[:240]
    '"Any person who violates section 506(a) (relating to criminal offenses) of title 17 shall be punished as provided in subsections (b), (c), and (d) and such penalties shall be in addition to any other provisions of title 17 or any other law.'


An important caveat for this feature is that the return value of the
:meth:`~legislice.enactments.BaseEnactment.cross_references` method will only be populated with internal links
that have been marked up in the United States Legislative Markup XML
published by the legislature. Unfortunately, some parts of the United
States Code don’t include any link markup when making references to
other legislation.

.. _downloading-enactments-from-inbound-citations:

Downloading Enactments from inbound citations
------------------------------------------------

The method in the previous section finds and downloads Enactments
cited by a known :class:`~legislice.enactments.Enactment`. But sometimes we want to discover
provisions that cite *to* a particular provision. These “inbound”
citations are not stored on the Python Enactment object. Instead, we
have to go back to the download client and make an API request to get
them, using the :meth:`~legislice.download.Client.citations_to` method.

In this example, we’ll get all the citations to the provision of the
United States Code cited ``/us/usc/t17/s501`` (in other
words, `Title 17, Section 501 <https://authorityspoke.com/legislice/us/usc/t17/s501/>`__).
This gives us all known provisions that cite to that node
in the document tree, regardless of whether different text has been
enacted at that node at different times.


    >>> inbound_refs = client.citations_to("/us/usc/t17/s501")
    >>> inbound_refs
    [InboundReference to /us/usc/t17/s501, from (/us/usc/t17/s109/b/4 2013-07-18),
     InboundReference to /us/usc/t17/s501, from (/us/usc/t17/s503/a/3 2013-07-18)]


We can examine one of these :class:`~legislice.enactments.InboundReference` objects to
see the text creating the citation.

    >>> inbound_refs[0].content
    'Any person who distributes a phonorecord or a copy of a computer program (including any tape, disk, or other medium embodying such program) in violation of paragraph (1) is an infringer of copyright under section 501 of this title and is subject to the remedies set forth in sections 502, 503, 504, and 505. Such violation shall not be a criminal offense under section 506 or cause such person to be subject to the criminal penalties set forth in section 2319 of title 18.'


But an :class:`~legislice.enactments.InboundReference` doesn’t have all the same information as an
:class:`~legislice.enactments.Enactment` object. Importantly, it doesn’t have the text of any
subsections nested inside the cited provision. We can use the download
:class:`~legislice.download.Client` again to convert the InboundReference into an Enactment.

    >>> citing_enactment = client.read(inbound_refs[0])
    >>> citing_enactment
    Enactment(source=/us/usc/t17/s109/b/4, start_date=2013-07-18, selection=TextPositionSet([TextPositionSelector[0, 472)]))

This Enactment happens not to have any child nodes nested within it, so
its full text is the same as what we saw when we looked at the
InboundReference’s content attribute.

    >>> citing_enactment.children
    []

Sometimes, an :class:`~legislice.enactments.InboundReference` has more than one citation and start
date. That means that the citing text has been enacted in different
places at different times. This can happen because the provisions of a
legislative code have been reorganized and renumbered. Here’s an
example. We’ll look for citations
to `Section 1301 of USC Title 2 <https://authorityspoke.com/legislice/us/usc/t2/s1301/>`__, which
is a section containing definitions of terms that will be used
throughout the rest of Title 2.

    >>> refs_to_definitions = client.citations_to("/us/usc/t2/s1301")
    [InboundReference to /us/usc/t2/s1301, from (/us/usc/t2/s4579/a/4/A 2018-05-09) and 2 other locations,
     InboundReference to /us/usc/t2/s1301, from (/us/usc/t2/s4579/a/5/A 2018-05-09) and 2 other locations,
     InboundReference to /us/usc/t2/s1301, from (/us/usc/t42/s2000ff/2/A/iii 2013-07-18),
     InboundReference to /us/usc/t2/s1301, from (/us/usc/t42/s2000ff/2/B/iii 2013-07-18)]

The :meth:`~legislice.download.Client.citations_to` method returns a list,
and two of the InboundReferences in this list have been enacted in three different
locations.

    >>> refs_to_definitions[0].locations
    [(/us/usc/t2/s60c-5/a/2/A 2013-07-18),
     (/us/usc/t2/s4579/a/2/A 2014-01-16),
     (/us/usc/t2/s4579/a/4/A 2018-05-09)]

When we pass an InboundReference to :meth:`~legislice.download.Client.read`, the download client
makes an :class:`~legislice.enactments.Enactment` from the most recent location where the citing
provision has been enacted.

    >>> client.read(refs_to_definitions[0])
    Enactment(source=/us/usc/t2/s4579/a/4/A, start_date=2018-05-09, selection=TextPositionSet([TextPositionSelector[0, 68)]))


If we need the :class:`~legislice.enactments.Enactment` representing the statutory text before it was
moved and renumbered, we can pass one of the :class:`~legislice.enactments.CitingProvisionLocation`
objects to the :class:`~legislice.download.Client` instead. Note that the Enactment we get
this way has the same content text, but a different citation node, an
earlier start date, and an earlier end date.

    >>> citing_enactment_before_renumbering = client.read(refs_to_definitions[0].locations[0])
    >>> citing_enactment_before_renumbering
    Enactment(source=/us/usc/t2/s60c-5/a/2/A, start_date=2013-07-18, selection=TextPositionSet([TextPositionSelector[0, 68)]))

    >>> citing_enactment_before_renumbering.end_date
    datetime.date(2014, 1, 16)
