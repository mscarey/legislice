.. _enactments:

Comparing Enactments
====================

This notebook will show how ``legislice`` provides convenient
functions for comparing passages of legislative text.

As explained in the :ref:`downloading` guide,
begin by creating a :class:`~legislice.download.Client` to download
and create :class:`~legislice.enactments.Enactment` objects.

.. code:: ipython3

    import os
    from dotenv import load_dotenv
    from legislice.download import Client

    load_dotenv()

    TOKEN = os.getenv("LEGISLICE_API_TOKEN")
    client = Client(api_token=TOKEN)

.. _features-of-an-enactment:

Features of an Enactment
---------------------------

Now let’s load the Fourteenth Amendment. We can get its effective date
as a Python :py:class:`datetime.date` object.

    >>> fourteenth_amendment = client.read(query="/us/const/amendment/XIV")
    >>> fourteenth_amendment.start_date
    datetime.date(1868, 7, 28)

We can also view its ``level``, which is “constitution”, as opposed to
“statute” or “regulation”.

    >>> fourteenth_amendment.level
    'constitution'

And we can find out the ``node``, or place in the document tree, for
the Fourteenth Amendment itself as well at its subsections.

    >>> fourteenth_amendment.node
    '/us/const/amendment/XIV'


    >>> fourteenth_amendment.children[0].node
    '/us/const/amendment/XIV/1'


We can also isolate some parts of the ``node`` path, such as the
``jurisdiction`` and ``code`` the amendment comes from.

    >>> fourteenth_amendment.jurisdiction
    'us'

    >>> fourteenth_amendment.code
    'const'

.. _selecting-text:

Selecting text
-----------------

When we use the :meth:`~legislice.enactments.Enactment.selected_text` method,
we get all the enacted text
in the `Fourteenth Amendment <https://authorityspoke.com/legislice/us/const/amendment/XIV>`__,
including all its subsections.

    >>> fourteenth_amendment.selected_text()
    'All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside. No State shall make or enforce any law which shall abridge the privileges or immunities of citizens of the United States; nor shall any State deprive any person of life, liberty, or property, without due process of law; nor deny to any person within its jurisdiction the equal protection of the laws. Representatives shall be apportioned among the several States according to their respective numbers, counting the whole number of persons in each State, excluding Indians not taxed. But when the right to vote at any election for the choice of electors for President and Vice President of the United States, Representatives in Congress, the Executive and Judicial officers of a State, or the members of the Legislature thereof, is denied to any of the male inhabitants of such State, being twenty-one years of age, and citizens of the United States, or in any way abridged, except for participation in rebellion, or other crime, the basis of representation therein shall be reduced in the proportion which the number of such male citizens shall bear to the whole number of male citizens twenty-one years of age in such State. No person shall be a Senator or Representative in Congress, or elector of President and Vice President, or hold any office, civil or military, under the United States, or under any State, who, having previously taken an oath, as a member of Congress, or as an officer of the United States, or as a member of any State legislature, or as an executive or judicial officer of any State, to support the Constitution of the United States, shall have engaged in insurrection or rebellion against the same, or given aid or comfort to the enemies thereof. But Congress may by a vote of two-thirds of each House, remove such disability. The validity of the public debt of the United States, authorized by law, including debts incurred for payment of pensions and bounties for services in suppressing insurrection or rebellion, shall not be questioned. But neither the United States nor any State shall assume or pay any debt or obligation incurred in aid of insurrection or rebellion against the United States, or any claim for the loss or emancipation of any slave; but all such debts, obligations and claims shall be held illegal and void. The Congress shall have power to enforce, by appropriate legislation, the provisions of this article.'

However, we might want an :class:`~legislice.enactments.Enactment` object that only represents a
part of the Fourteenth Amendment that’s relevant to a particular case.
We can use the :meth:`~legislice.enactments.Enactment.select` method to limit the text of the provision
that’s considered “selected”. One way to do this is with a series of
strings that exactly match the text we want to select. Because we're selecting only some of
the text, the output of the ``selected_text`` method will be different.

    >>> fourteenth_amendment.select(["No State shall", "deprive any person of", "liberty", "without due process of law"])
    >>> fourteenth_amendment.selected_text()
    '…No State shall…deprive any person of…liberty…without due process of law…'


Every time we use the :meth:`~legislice.enactments.Enactment.select` method, it clears any existing text
selection from the Enactment. But if we want to select additional text
without clearing the existing selection, we can
use :meth:`~legislice.enactments.Enactment.select_more`.
It’s okay if the selection we pass in
to :meth:`~legislice.enactments.Enactment.select_more` overlaps with
text we've already selected.

    >>> fourteenth_amendment.select_more("life, liberty, or property,")
    >>> fourteenth_amendment.selected_text()
    '…No State shall…deprive any person of life, liberty, or property, without due process of law…'

If we need to select a passage that occurs more than once in the
Enactment, we can import the :class:`anchorpoint.textselectors.TextQuoteSelector` class instead of
using strings. With a :class:`~anchorpoint.textselectors.TextQuoteSelector`, we specify not just the
``exact`` phrase we want to select, but also a ``prefix`` or ``suffix``
that makes the phrase uniquely identifiable. In this example, the text
being selected is the second instance of the phrase “twenty-one years of
age” in the Fourteenth Amendment.

    >>> from legislice.enactments import TextQuoteSelector
    >>> fourteenth_amendment.select(TextQuoteSelector(prefix="male citizens ", exact="twenty-one years of age"))
    >>> fourteenth_amendment.selected_text()
    '…twenty-one years of age…'

We can also access the start and endpoints of the quoted passages, but
there’s a potential source of confusion: the ``selection`` attribute
only provides the selected parts of the current node, not of
the child nodes. For the Fourteenth Amendment, that will return an empty
set because all of the Fourteenth Amendment’s text is nested within
numbered sections.

    >>> fourteenth_amendment.selection
    TextPositionSet{}

To see the positions of the selected text in the child nodes as well,
we need to use :meth:`~legislice.enactments.Enactment.tree_selection`.
This is a method, not an attribute,
so we need to include the parentheses at the end of the statement to
make it work. In this example, the selected phrase “twenty-one years of
age” starts on the 1254th character of the Fourteenth Amendment’s text.

    >>> fourteenth_amendment.tree_selection()
    TextPositionSet{TextPositionSelector[1254, 1277)}

We could also look at the ``selection`` attributes of the child nodes
to see the positions of their selected text. But note: if we access the
``selection`` attribute on `section 2 of the Fourteenth
Amendment <https://authorityspoke.com/legislice/us/const/amendment/XIV/2>`__, then
the starting index of the selected passage is counted from the beginning
of section 2, not from the beginning of the entire Fourteenth Amendment.

    >>> fourteenth_amendment.children[1].selection
    TextPositionSet{TextPositionSelector[786, 809)}

If we happen to know the start and end indices of the passage we want,
then we can use a :class:`~anchorpoint.textselectors.TextPositionSelector` or
:class:`~anchorpoint.textselectors.TextPositionSet` to
select it, instead of specifying the exact text.

    >>> from legislice.enactments import TextPositionSelector, TextPositionSet
    >>> fourteenth_amendment.select(TextPositionSet([TextPositionSelector(1921, 1973), TextPositionSelector(2111, 2135)]))
    >>> fourteenth_amendment.selected_text()
    '…The validity of the public debt of the United States…shall not be questioned.…'

.. _comparing-selected-text:

Comparing selected text
--------------------------

Legislice provides methods for comparing the selected text in
Enactments. To get started, we’ll use Python’s :py:func:`copy.deepcopy` function to
make a copy of the Enactment we were working on at the end of :ref:`selecting-text`.
(If we used regular :py:func:`~copy.copy` instead of :py:func:`~copy.deepcopy`,
then making changes to the copy could cause changes to the original,
which would be confusing.)

    >>> from copy import deepcopy
    >>> public_debt_provision = deepcopy(fourteenth_amendment.children[3])
    >>> public_debt_provision.selected_text()
    'The validity of the public debt of the United States…shall not be questioned.…'

Next, we’ll change the selected text of the
original :class:`~legislice.enactments.Enactment` to
include all the text that was selected before, plus more.

    >>> fourteenth_amendment.select(TextPositionSelector(1921, 2135))
    >>> fourteenth_amendment.selected_text()
    '…The validity of the public debt of the United States, authorized by law, including debts incurred for payment of pensions and bounties for services in suppressing insurrection or rebellion, shall not be questioned.…'

Now we can compare the text selections in these two Enactments. The
:meth:`~legislice.enactments.Enactment.implies` method checks whether the Enactment
on the left has all thetext of the Enactment on the right.
The :meth:`~legislice.enactments.Enactment.means` method checks whether
they both have the same text.

    >>> fourteenth_amendment.implies(public_debt_provision)
    True

We can also use Python’s built-in “greater than or equal” operator as
an alias for the :meth:`~legislice.enactments.Enactment.implies` method.

    >>> fourteenth_amendment >= public_debt_provision
    True

Notice that Legislice is able to compare these two passages even though
``amendment`` is a text selection from the entire Fourteenth Amendment,
while ``public_debt_provision`` is a text selection from only section 4
of the Fourteenth Amendment. We can verify this by checking the “node”
attribute on each Enactment.

    >>> fourteenth_amendment.node
    '/us/const/amendment/XIV'

    >>> public_debt_provision.node
    '/us/const/amendment/XIV/4'

To determine whether two Enactments have the same text (and
neither has any more than the other), use
the :meth:`~legislice.enactments.Enactment.means` method. Here’s
how we can check that the Fifth Amendment doesn’t have identical text
to the first section of the Fourteenth Amendment.

    >>> fifth_amendment = client.read(query="/us/const/amendment/V")
    >>> fifth_amendment.selected_text()
    'No person shall be held to answer for a capital, or otherwise infamous crime, unless on a presentment or indictment of a Grand Jury, except in cases arising in the land or naval forces, or in the Militia, when in actual service in time of War or public danger; nor shall any person be subject for the same offence to be twice put in jeopardy of life or limb; nor shall be compelled in any Criminal Case to be a witness against himself; nor be deprived of life, liberty, or property, without due process of law; nor shall private property be taken for public use, without just compensation.'

    >>> fourteenth_amendment_section_1 = client.read(query="/us/const/amendment/XIV/1")
    >>> fifth_amendment.means(fourteenth_amendment_section_1)
    False

However, the Fifth Amendment and the first section of the Fourteenth
Amendment both happen to contain the phrase “life, liberty, or property,
without due process of law”. If we select that same passage from both
provisions, then we can use the :meth:`~legislice.enactments.Enactment.means`
method to verify that both text selections are identical.

    >>> phrase = "life, liberty, or property, without due process of law"
    >>> fourteenth_amendment_section_1.select(phrase)
    >>> fifth_amendment.select(phrase)
    >>> fourteenth_amendment_section_1.means(fifth_amendment)
    True

There are many situations in real legal analysis where it’s helpful to
know if identical text has been enacted at different citations. It could
mean that the identical section has been renumbered, or it could mean
that a judicial interpretation of one Enactment is also relevant to the
other Enactment. Legislice’s :meth:`~legislice.enactments.Enactment.implies`
and :meth:`~legislice.enactments.Enactment.means` methods can help
to automate that analysis.

Since we can use ``>=`` as an alias
for :meth:`~legislice.enactments.Enactment.implies`, we might expect
to be able to use ``==`` as an alias
for :meth:`~legislice.enactments.Enactment.means`. Currently we can’t
do that, because overriding the equals function could interfere with
Python’s ability to determine what objects are identical, and could
cause bugs that would be difficult to diagnose. However, we can use
``>`` as an alias that returns ``True`` only
if :meth:`~legislice.enactments.Enactment.implies` would return
``True`` while :meth:`~legislice.enactments.Enactment.means` would return ``False``.

.. _combining-enactments:

Combining Enactments
-----------------------

When we have two Enactments and either they are at the same node or one
is a descendant of the other, we can combine them into a new Enactment
using the addition sign. Here’s an example from a copyright statute in
the United States Code. The example shows that we can load section
``/us/usc/t17/s103``, select some text from subsection ``b`` of that
provision, and then add it to a separate Enactment representing the
entirety of subsection ``/us/usc/t17/s103/a``. Legislice combines the
text from subsection ``a`` and subsection ``b`` in the correct order.

    >>> s103 = client.read(query="/us/usc/t17/s103", date="2020-01-01")
    >>> selections = ["The copyright in such work is independent of", "any copyright protection in the preexisting material."]
    >>> s103.select(selections)
    >>> s103.selected_text()
    '…The copyright in such work is independent of…any copyright protection in the preexisting material.'

    >>> s103a = client.read(query="/us/usc/t17/s103/a", date="2020-01-01")
    >>> s103a.selected_text()
    'The subject matter of copyright as specified by section 102 includes compilations and derivative works, but protection for a work employing preexisting material in which copyright subsists does not extend to any part of the work in which such material has been used unlawfully.'

    >>> combined_enactment = s103 + s103a
    >>> combined_enactment.selected_text()
    'The subject matter of copyright as specified by section 102 includes compilations and derivative works, but protection for a work employing preexisting material in which copyright subsists does not extend to any part of the work in which such material has been used unlawfully.…The copyright in such work is independent of…any copyright protection in the preexisting material.'

.. _converting-enactments-to-json:

Converting Enactments to JSON
--------------------------------

When we want a representation of a legislative passage that’s precise,
machine-readable, and easy to share over the internet, we can use
Legislice’s JSON schema. Here’s how to convert the Enactment object
called ``combined_enactment``, which was created in the example above,
to JSON.

As explained in the section above, this JSON represents a selection of three
nonconsecutive passages from the most recent version of
`section 103 of Title 17 of the United States Code <https://authorityspoke.com/legislice/us/usc/t17/s103@2020-11-17>`__.
The schema's :meth:`~marshmallow.Schema.dumps` method returns a JSON string,
while the :meth:`~marshmallow.Schema.dump` method returns a
Python dictionary.

    >>> from legislice.schemas import EnactmentSchema
    >>> schema = EnactmentSchema()
    >>> schema.dumps(combined_enactment)
    '{"node": "/us/usc/t17/s103", "heading": "Subject matter of copyright: Compilations and derivative works", "text_version": null, "start_date": "2013-07-18", "end_date": null, "selection": [], "anchors": [], "children": [{"node": "/us/usc/t17/s103/a", "heading": "", "text_version": {"content": "The subject matter of copyright as specified by section 102 includes compilations and derivative works, but protection for a work employing preexisting material in which copyright subsists does not extend to any part of the work in which such material has been used unlawfully."}, "start_date": "2013-07-18", "end_date": null, "selection": [{"start": 0, "end": 277}], "anchors": [], "children": []}, {"node": "/us/usc/t17/s103/b", "heading": "", "text_version": {"content": "The copyright in a compilation or derivative work extends only to the material contributed by the author of such work, as distinguished from the preexisting material employed in the work, and does not imply any exclusive right in the preexisting material. The copyright in such work is independent of, and does not affect or enlarge the scope, duration, ownership, or subsistence of, any copyright protection in the preexisting material."}, "start_date": "2013-07-18", "end_date": null, "selection": [{"start": 256, "end": 300}, {"start": 384, "end": 437}], "anchors": [], "children": []}]}'

Formatting Citations (Experimental)
--------------------------------------

Legislice has preliminary support for serializing citations for
Enactment objects based on `Citation Style Language
JSON <https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html>`__.
The goal of this feature is to support compatibility with
`Jurism <https://juris-m.github.io/>`__. Please `open an issue in the
Legislice repo <https://github.com/mscarey/legislice/issues>`__ if you
have suggestions for how this feature should develop to support your use
case.

    >>> cares_act_benefits = client.read("/us/usc/t15/s9021/")
    >>> cares_act_benefits.heading
    'Pandemic unemployment assistance'
    >>> citation = cares_act_benefits.as_citation()
    >>> str(citation)
    '15 U.S. Code § 9021 (2020)'
    >>> cares_act_benefits.csl_json()
    '{"container-title": "U.S. Code", "jurisdiction": "us", "volume": "15", "event-date": {"date-parts": [["2020", 4, 10]]}, "type": "legislation", "section": "sec. 9021"}'

This CSL-JSON format currently only identifies the cited provision down
to the section level. A citation to a subsection or deeper nested
provision will be the same as a citation to its parent section.