Downloading Legislation
=======================================

Legislice is a utility for downloading the text of statutes and
constitutional provisions, and then creating computable objects
representing passages from those provisions. This guide will show you
how to get started.

Legislice depends on the `AuthoritySpoke
API <https://authorityspoke.com/>`__ as its source of legislative text.
Currently the API serves the text of the United States Constitution,
plus versions of the United States Code in effect since 2013. Provisions
of the United States Code that were repealed prior to 2013 aren’t yet
available through the API, and neither are any regulations or any state
law.

1. Using an API token
---------------------

To get started, `make an account on
authorityspoke.com <https://authorityspoke.com/account/signup/>`__. Then
go to the `User Profile
page <https://authorityspoke.com/account/profile/>`__, where you can
find your API token. The token is a 40-character string of random
letters and numbers. You’ll be sending this token to AuthoritySpoke to
validate each API request, and you should keep it secret as you would a
password.

There are several ways you can access your API token in Python. One way
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
Python working file or notebook. That makes it easier for you to avoid
accidentally publishing the API token or sharing it with unauthorized
people.

Here’s an example of loading an API token from a ``.env`` file using
``dotenv``.

.. code:: ipython3

    import os
    from dotenv import load_dotenv
    load_dotenv()

    TOKEN = os.getenv("LEGISLICE_API_TOKEN")

Now you can use the API token to create a Legislice ``Client`` object.
This object holds your API token, so you can reuse the ``Client``
without re-entering your API token repeatedly.

.. code:: ipython3

    from legislice.download import Client
    client = Client(api_token=TOKEN)

2. Fetching a provision from the API
------------------------------------

To download legislation using the ``Client``, you must specify a
``path`` to the provision you want, and optionally you can specify the
``date`` of the version of the provision you want. If you don’t specify
a date, you’ll be given the most recent version of the provision.

The ``path`` citation format is based on the section identifiers in the
`United States Legislative Markup
standard <https://uscode.house.gov/download/resources/USLM-User-Guide.pdf>`__,
which is a United States government standard used by the Office of the
Law Revision Counsel for publishing the United States Code. Similar to a
URL path in a web address, the ``path`` format is a series of labels
connected with forward slashes. The first part identifies the
jurisdiction, the second part (if any) identifies the legislative code
within that jurisdiction, and so on.

If you don’t know the right citation for the provision you want, you can
browse the `directory of available
provisions <https://authorityspoke.com/legislice/>`__, where the links
to each provision show the correct ``path`` for that provision. Or, if
you’re signed in to your AuthoritySpoke account, you can browse an `HTML
version of the API itself <https://authorityspoke.com/api/v1/>`__. If
you see the error message “Authentication credentials were not
provided”, that means you aren’t signed in, and you might want to go
back to the `login page <https://authorityspoke.com/account/login/>`__.

Here’s an example of how to fetch the text of the Fourth Amendment using
the ``Client``.

.. code:: ipython3

    fourth_a = client.fetch(path="/us/const/amendment/IV")

The ``client.fetch`` method made an API call to AuthoritySpoke, and
return JSON that has been converted to a Python ``dict``. There are
fields representing the ``content`` of the provision, the ``start_date``
when the provision went into effect, and more.

.. code:: ipython3

    fourth_a




.. parsed-literal::

    {'heading': 'AMENDMENT IV.',
     'content': 'The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized.',
     'children': [],
     'end_date': None,
     'node': '/us/const/amendment/IV',
     'start_date': '1791-12-15',
     'url': 'https://authorityspoke.com/api/v1/us/const/amendment/IV/',
     'parent': 'https://authorityspoke.com/api/v1/us/const/amendment/'}



3. Loading an Enactment object
------------------------------

If all you needed was to get a JSON response from the API, you could
have used a more general Python library like ``requests``. Legislice
also lets you load the JSON response as an ``Enactment`` object, which
has methods that allow you to select some but not all of the provision’s
text. One way to load an ``Enactment`` is with the
``Client.read_from_json`` method.

.. code:: ipython3

    client.read_from_json(fourth_a)




.. parsed-literal::

    Enactment(source=/us/const/amendment/IV, start_date=1791-12-15, selection=TextPositionSet([TextPositionSelector[0, 332)]))



Instead of always using ``Client.fetch`` followed by
``Client.read_from_json``, you can combine the two functions together
with ``Client.read``. In this example, I’ll use ``Client.read`` load a
constitutional amendment that contains subsections, to show that the
structure of the amendment is preserved in the resulting ``Enactment``
object.

.. code:: ipython3

    thirteenth_a = client.read(path="/us/const/amendment/XIII")

The string representation of this provision includes both the selected
text (which is the full text of the amendment) as well as a citation to
the provision with its effective date.

Currently the only supported citation format is the path-style citation
used in United States Legislative Markup. Future versions of Legislice
may support the ability to convert to traditional statute citation
styles.

.. code:: ipython3

    str(thirteenth_a)




.. parsed-literal::

    '"Neither slavery nor involuntary servitude, except as a punishment for crime whereof the party shall have been duly convicted, shall exist within the United States, or any place subject to their jurisdiction. Congress shall have power to enforce this article by appropriate legislation." (/us/const/amendment/XIII 1865-12-18)'



The text of the Thirteenth Amendment is all within Section 1 and Section
2 of the amendment. You can use the ``Enactment.children`` property to
get a list of provisions contained within an ``Enactment``.

.. code:: ipython3

    thirteenth_a.children




.. parsed-literal::

    [Enactment(source=/us/const/amendment/XIII/1, start_date=1865-12-18, selection=TextPositionSet([TextPositionSelector[0, 207)])),
     Enactment(source=/us/const/amendment/XIII/2, start_date=1865-12-18, selection=TextPositionSet([TextPositionSelector[0, 77)]))]



Then you can access each child provision as its own ``Enactment`` object
from the ``children`` list. Remember that lists in Python start at index
0, so if you want Section 2, you’ll find it at index 1 of the
``children`` list.

.. code:: ipython3

    str(thirteenth_a.children[1])




.. parsed-literal::

    '"Congress shall have power to enforce this article by appropriate legislation." (/us/const/amendment/XIII/2 1865-12-18)'



4. Downloading prior versions of an Enactment
---------------------------------------------

The API can be used to access specific provisions deeply nested within
the United States Code, and also to access multiple date versions of the
same provision. Here’s a subsection of an appropriations statute as of
2015. We can use the ``end_date`` attribute to find when this version of
the statute was displaced by a new version.

.. code:: ipython3

    old_grant_objective = client.read(path="/us/usc/t42/s300hh-31/a/1", date="2015-01-01")

.. code:: ipython3

    old_grant_objective.content




.. parsed-literal::

    'strengthening epidemiologic capacity to identify and monitor the occurrence of infectious diseases and other conditions of public health importance;'



.. code:: ipython3

    str(old_grant_objective.end_date)




.. parsed-literal::

    '2019-07-05'



And here’s the same provision as of 2020.

.. code:: ipython3

    new_grant_objective = client.read(path="/us/usc/t42/s300hh-31/a/1", date="2020-01-01")

.. code:: ipython3

    new_grant_objective.content




.. parsed-literal::

    'strengthening epidemiologic capacity to identify and monitor the occurrence of infectious diseases, including mosquito and other vector-borne diseases, and other conditions of public health importance;'



.. code:: ipython3

    str(new_grant_objective.end_date)




.. parsed-literal::

    'None'



5. Exploring the Structure of a Legislative Code
------------------------------------------------

When you query the API for a provision at a path with less than four
parts (e.g., when you query for an entire Title of the United States
Code), the response doesn’t include the full text of the provision’s
children. Instead, it only contains URLs that link to the child nodes.
This might help you automate the process of navigating the API and
discovering the provisions you want. Here’s an example that discovers
the URLs for the articles of the US Constitution.

.. code:: ipython3

    articles = client.read(path="/us/const/article")

.. code:: ipython3

    articles.children




.. parsed-literal::

    ['https://authorityspoke.com/api/v1/us/const/article/I/',
     'https://authorityspoke.com/api/v1/us/const/article/II/',
     'https://authorityspoke.com/api/v1/us/const/article/III/',
     'https://authorityspoke.com/api/v1/us/const/article/IV/',
     'https://authorityspoke.com/api/v1/us/const/article/V/',
     'https://authorityspoke.com/api/v1/us/const/article/VI/',
     'https://authorityspoke.com/api/v1/us/const/article/VII/']


