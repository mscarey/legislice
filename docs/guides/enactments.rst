.. _enactments:

Comparing Enactments
====================

This notebook will show how ``legislice`` provides convenient
functions for comparing passages of legislative text.

As explained in the :ref:`downloading` guide,
begin by creating a :class:`~legislice.download.Client` to download
and create :class:`~legislice.enactments.Enactment` objects.

    >>> import os
    >>> from dotenv import load_dotenv
    >>> from legislice.download import Client
    >>> load_dotenv()
    True
    >>> TOKEN = os.getenv("LEGISLICE_API_TOKEN")
    >>> client = Client(api_token=TOKEN)

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
    <CodeLevel.CONSTITUTION: 1>

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

When we use the :meth:`~legislice.enactments.Enactment.text` method,
we get all the enacted text
in the `Fourteenth Amendment <https://authorityspoke.com/legislice/us/const/amendment/XIV>`__,
including all its subsections.

    >>> fourteenth_amendment.text
    'All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside. No State shall make or enforce any law which shall abridge the privileges or immunities of citizens of the United States; nor shall any State deprive any person of life, liberty, or property, without due process of law; nor deny to any person within its jurisdiction the equal protection of the laws. Representatives shall be apportioned among the several States according to their respective numbers, counting the whole number of persons in each State, excluding Indians not taxed. But when the right to vote at any election for the choice of electors for President and Vice President of the United States, Representatives in Congress, the Executive and Judicial officers of a State, or the members of the Legislature thereof, is denied to any of the male inhabitants of such State, being twenty-one years of age, and citizens of the United States, or in any way abridged, except for participation in rebellion, or other crime, the basis of representation therein shall be reduced in the proportion which the number of such male citizens shall bear to the whole number of male citizens twenty-one years of age in such State. No person shall be a Senator or Representative in Congress, or elector of President and Vice President, or hold any office, civil or military, under the United States, or under any State, who, having previously taken an oath, as a member of Congress, or as an officer of the United States, or as a member of any State legislature, or as an executive or judicial officer of any State, to support the Constitution of the United States, shall have engaged in insurrection or rebellion against the same, or given aid or comfort to the enemies thereof. But Congress may by a vote of two-thirds of each House, remove such disability. The validity of the public debt of the United States, authorized by law, including debts incurred for payment of pensions and bounties for services in suppressing insurrection or rebellion, shall not be questioned. But neither the United States nor any State shall assume or pay any debt or obligation incurred in aid of insurrection or rebellion against the United States, or any claim for the loss or emancipation of any slave; but all such debts, obligations and claims shall be held illegal and void. The Congress shall have power to enforce, by appropriate legislation, the provisions of this article.'

However, we might want an :class:`~legislice.enactments.Enactment` object that only represents a
part of the Fourteenth Amendment that’s relevant to a particular case.
We can use the :meth:`~legislice.enactments.Enactment.select` method to limit the text of the provision
that’s considered “selected”. One way to do this is with a series of
strings that exactly match the text we want to select. Because we're selecting only some of
the text, the output of the :meth:`~legislice.enactments.EnactmentPassage.selected_text` method
will be different.

    >>> passages = fourteenth_amendment.select(["No State shall", "deprive any person of", "liberty", "without due process of law"])
    >>> passages.selected_text()
    '…No State shall…deprive any person of…liberty…without due process of law…'

The :meth:`~legislice.enactments.Enactment.select` method returns a new
:class:`~legislice.enactments.EnactmentPassage` object, which holds
both the :class:`~legislice.enactments.Enactment` and a
:class:`~anchorpoint.textselectors.TextPositionSet` indicating which text is
selected. But if we want to select additional text
without clearing the existing selection, we can
use the EnactmentPassage's :meth:`~legislice.enactments.EnactmentPassage.select_more`
method. It’s okay if the selection we pass in
to :meth:`~legislice.enactments.EnactmentPassage.select_more` overlaps
with text we've already selected.

    >>> passages.select_more("life, liberty, or property,")
    >>> passages.selected_text()
    '…No State shall…deprive any person of life, liberty, or property, without due process of law…'

If we need to select a passage that occurs more than once in the
Enactment, we can import the :class:`~anchorpoint.textselectors.TextQuoteSelector` class instead of
using strings. With a :class:`~anchorpoint.textselectors.TextQuoteSelector`, we specify not just the
``exact`` phrase we want to select, but also a ``prefix`` or ``suffix``
that makes the phrase uniquely identifiable. In this example, the text
being selected is the second instance of the phrase “twenty-one years of
age” in the Fourteenth Amendment.

    >>> from legislice import TextQuoteSelector
    >>> age_passage = fourteenth_amendment.select(TextQuoteSelector(prefix="male citizens ", exact="twenty-one years of age"))
    >>> age_passage.selected_text()
    '…twenty-one years of age…'

If we happen to know the start and end indices of the passage we want,
then we can use a :class:`~anchorpoint.textselectors.TextPositionSelector` or
:class:`~anchorpoint.textselectors.TextPositionSet` to
select it, instead of specifying the exact text.

    >>> from legislice.enactments import TextPositionSelector, TextPositionSet
    >>> amendment_passage = fourteenth_amendment.select(TextPositionSet(positions=[TextPositionSelector(start=1921, end=1973), TextPositionSelector(start=2111, end=2135)]))
    >>> amendment_passage.selected_text()
    '…The validity of the public debt of the United States…shall not be questioned.…'

We can also use the method :meth:`~legislice.enactments.EnactmentPassage.child_passages`
to get a new :class:`~legislice.enactments.EnactmentPassage` with only the subsection
of the Fourteenth Amendment that interests us. The citation stored in the ``node`` attribute
is now different, but the text selector still remains in
place, so we can still get the same selected text.

    >>> public_debt_provision = amendment_passage.child_passages[3]
    >>> public_debt_provision.node
    '/us/const/amendment/XIV/4'
    >>> public_debt_provision.selected_text()
    'The validity of the public debt of the United States…shall not be questioned.…'

.. _comparing-selected-text:

Comparing Selected Text
--------------------------

Next, we’ll create a new :class:`~legislice.enactments.EnactmentPassage` to compare by
changing the selected text of the original :class:`~legislice.enactments.Enactment` to
include all the text that was selected before, plus more.

    >>> debt_passage = fourteenth_amendment.select(TextPositionSelector(start=1921, end=2135))
    >>> debt_passage.selected_text()
    '…The validity of the public debt of the United States, authorized by law, including debts incurred for payment of pensions and bounties for services in suppressing insurrection or rebellion, shall not be questioned.…'

Now we can compare the text selections in these
two :class:`~legislice.enactments.EnactmentPassage`\s. The
:meth:`~legislice.enactments.Enactment.implies` method checks whether the Enactment
on the left has all the text of the Enactment on the right.
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
    >>> fifth_amendment.text
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
    >>> due_process_14 = fourteenth_amendment_section_1.select(phrase)
    >>> due_process_5 = fifth_amendment.select(phrase)
    >>> due_process_14.means(due_process_5)
    True

There are many situations in real legal analysis where it’s helpful to
know if identical text has been enacted at different citations. It could
mean that the identical section has been renumbered, or it could mean
that a judicial interpretation of one Enactment is also relevant to the
other Enactment. Legislice’s :meth:`~legislice.enactments.Enactment.implies`
and :meth:`~legislice.enactments.Enactment.means` methods can help
to automate that analysis.

Since ``>=`` is an alias
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
    >>> s103_passage = s103.select(selections)
    >>> s103_passage.selected_text()
    '…The copyright in such work is independent of…any copyright protection in the preexisting material.'

    >>> s103a = client.read(query="/us/usc/t17/s103/a", date="2020-01-01")
    >>> s103a.text
    'The subject matter of copyright as specified by section 102 includes compilations and derivative works, but protection for a work employing preexisting material in which copyright subsists does not extend to any part of the work in which such material has been used unlawfully.'

    >>> combined_passage = s103_passage + s103a
    >>> combined_passage.selected_text()
    'The subject matter of copyright as specified by section 102 includes compilations and derivative works, but protection for a work employing preexisting material in which copyright subsists does not extend to any part of the work in which such material has been used unlawfully.…The copyright in such work is independent of…any copyright protection in the preexisting material.'

.. _enactment-groups:

EnactmentGroups
---------------

When we want to work with groups of Enactments that may or may not be
nested inside one another, we can put them together in
an :class:`~legislice.groups.EnactmentGroup`\.
When we create a new EnactmentGroup
or :meth:`~legislice.groups.EnactmentGroup.__add__` two
EnactmentGroups together, any overlapping
:class:`~legislice.enactments.Enactment`\s inside
will be combined into a single Enactment.

In this example, we create two EnactmentGroups called ``left`` and
``right``, each containing two Enactments, and add them together.
Because one of the Enactments
in ``left`` overlaps with one of the Enactments in ``right``, when we
add ``left`` and ``right`` together those two Enactments will be
combined into one. Thus the resulting EnactmentGroup will contain three
Enactments instead of four.

    >>> from legislice import EnactmentGroup
    >>> first = client.read(query="/us/const/amendment/I")
    >>> establishment_clause=first.select("Congress shall make no law respecting an establishment of religion")
    >>> speech_clause = first.select(["Congress shall make no law", "abridging the freedom of speech"])
    >>> second = client.read(query="/us/const/amendment/II")
    >>> arms_clause = second.select("the right of the people to keep and bear arms, shall not be infringed.")
    >>> third = client.read(query="/us/const/amendment/III")
    >>> left = EnactmentGroup(passages=[establishment_clause, arms_clause])
    >>> right = EnactmentGroup(passages=[third, speech_clause])
    >>> combined = left + right
    >>> print(combined)
    the group of Enactments:
      "Congress shall make no law respecting an establishment of religion…abridging the freedom of speech…" (/us/const/amendment/I 1791-12-15)
      "…the right of the people to keep and bear arms, shall not be infringed." (/us/const/amendment/II 1791-12-15)
      "No soldier shall, in time of peace be quartered in any house, without the consent of the Owner, nor in time of war, but in a manner to be prescribed by law." (/us/const/amendment/III 1791-12-15)
    >>> len(combined)
    3

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
`section 103 of Title 17 of the United States Code <https://authorityspoke.com/legislice/us/usc/t17/s103@2020-11-17/>`__.
The schema's :meth:`~legislice.enactments.Enactment.json` method returns a JSON string,
while the :meth:`~legislice.enactments.Enactment.dict` method returns a
Python dictionary.

    >>> combined.passages[0].json()
    '{"enactment": {"node": "/us/const/amendment/I", "start_date": "1791-12-15", "heading": "AMENDMENT I.", "text_version": {"content": "Congress shall make no law respecting an establishment of religion, or prohibiting the free exercise thereof; or abridging the freedom of speech, or of the press; or the right of the people peaceably to assemble, and to petition the Government for a redress of grievances.", "url": "https://authorityspoke.com/api/v1/textversions/735703/", "id": 735703}, "end_date": null, "first_published": "1788-06-21", "earliest_in_db": "1788-06-21", "anchors": [], "citations": [], "name": "", "children": []}, "selection": {"positions": [{"start": 0, "end": 66}, {"start": 113, "end": 144}], "quotes": []}}'

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
    '{"jurisdiction": "us", "code_level_name": "CodeLevel.STATUTE", "volume": "15", "section": "sec. 9021", "type": "legislation", "container-title": "U.S. Code", "event-date": {"date-parts": [["2020", 4, 10]]}}'

This CSL-JSON format currently only identifies the cited
provision down to the section level. Calling
the :meth:`~legislice.enactments.Enactment.as_citation` method
on a subsection or deeper nested provision will produce
the same citation data as its parent section.
