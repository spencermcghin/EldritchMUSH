"""The King's Laws and the Punishments of Arnesse — drawn from the
canonical PDFs in the Drive's Laws and Punishments folder.

These entries inform any NPC who would have lived under the Crown's
laws (which is everyone except the wholly lawless). NPCs reference
crimes by name (treason, theft, murder, oath-breaking) and know what
fate awaits the guilty.
"""
from world.canon import ENTRIES, CanonEntry as _E

ENTRIES.extend([
    _E(
        title="The King's Laws (Eleven Crimes)",
        text=(
            "By order of His Grace, Giles Bannon II, King of the Ardan, "
            "Lord Sovereign of the Seven Protectorates and Defender of "
            "the Vale, the following are the punishable crimes of the "
            "realm: I. unlawful and premeditated killing (except in war or "
            "duel); II. concealment of an unlawful act; III. betrayal of "
            "an oath, allegiance, or loyalty; IV. unlawful impersonation; "
            "V. unlawful assault; VI. thievery or transport of stolen "
            "property; VII. possession of illegal goods; VIII. lying — "
            "especially under oath; IX. tax evasion; X. refusing to be "
            "disarmed when commanded; XI. refusing to heed the King's "
            "command. The Crown decrees, the lords enforce."
        ),
    ),
    _E(
        title="Law: Murder and Concealment",
        text=(
            "Murder is illegal in all forms, but punishment scales with "
            "rank. A commoner who kills a noble faces execution or serious "
            "mutilation; a noble who kills a commoner often resolves it "
            "with a fine paid to the injured party. Concealment — hiding a "
            "crime after committing it — adds severity to whatever was "
            "done. Hidden bodies always worsen the sentence. Death in war "
            "is not murder by the law, a loophole that has covered much "
            "collateral cruelty."
        ),
    ),
    _E(
        title="Law: Treason — Punished Equally",
        text=(
            "Treason is one of the few crimes punished equally across all "
            "social ranks. Commoners or nobles who break oaths or plot "
            "against a noble or the Kingdom are treasonous. Punishment is "
            "almost always execution, usually in a public, very painful "
            "way — meant as example. The grim joke about treason: it is "
            "the crime of the defeated. A successful plot of treason "
            "often allows the victor to avoid being held to account at all."
        ),
    ),
    _E(
        title="Law: Theft, Possession, Smuggling",
        text=(
            "Thievery rarely brings execution but commonly brings "
            "confiscation, mutilation (the hand that stole), fines, or "
            "imprisonment. Smuggling counts as both theft and possession. "
            "Possession of illegal goods — most poisons, certain drugs, "
            "rare items, stolen property — is punished by confiscation, "
            "fines, imprisonment, or mutilation. The hand and the eye "
            "are common takings."
        ),
    ),
    _E(
        title="Law: Lying, Taxes, Disarmament, Obedience",
        text=(
            "Lying is a minor offense; lying under oath is serious — "
            "demotion, fines, humiliation, occasionally mutilation of the "
            "tongue. Taxes are owed by everyone but the Crown; failure to "
            "pay brings fines, imprisonment, or confiscation for "
            "commoners — and threats or invasion for nobles who default "
            "to their liege. Any noble may demand to disarm anyone in "
            "any setting before speaking with them; refusal is its own "
            "crime. Disobedience to a noble or significant rank is the "
            "lightest offense — usually exile, fine, demotion, or "
            "humiliation."
        ),
    ),
    _E(
        title="Punishment: Execution",
        text=(
            "Execution is reserved for the gravest crimes — murder, "
            "treason. It is often a public spectacle, slow and painful "
            "(hanging, sometimes drawing and quartering of the still-"
            "living). Nobles condemned to death are often given the mercy "
            "of private beheading by a headsman rather than the gallows. "
            "Execution ends a life; in folk-speech, it is the only "
            "punishment that 'closes the ledger.'"
        ),
    ),
    _E(
        title="Punishment: Exile and Imprisonment",
        text=(
            "Exile is mercy for the worst crimes — banishment from the "
            "noble's lands or the whole Kingdom under pain of death if "
            "seen again. Often combined with confiscation, mutilation, or "
            "fines. Imprisonment is simpler — local jail or one further "
            "afield. Some nobles will accept payment for release; some "
            "characters argue you out. Without rescue, jail is often the "
            "end of a life."
        ),
    ),
    _E(
        title="Punishment: Mutilation and Confiscation",
        text=(
            "Mutilation is the removal of hands, fingers, feet, eyes, or "
            "the application of scars or brands. The crime shapes the "
            "mutilation: the hand of a thief; the sword-hand of an "
            "assaulter; fingers for smuggling; eyes for impersonation; "
            "tongues for insolence to one's betters. The mark is "
            "permanent. Confiscation takes goods or coin in recompense "
            "for loss — often used when the guilty cannot pay a fine in "
            "silver."
        ),
    ),
    _E(
        title="Punishment: Demotion, Indenturement, Humiliation, Fines",
        text=(
            "Demotion strips a title or a position — Freemen and Artisans "
            "may be reduced to Serf; Highfolk and Nobles cannot. "
            "Indenturement places one in service to the noble or the "
            "injured party until a debt is worked off — typically used "
            "when a fine cannot be paid. Humiliation has two forms: "
            "public apology before peers (most common for nobles), or "
            "physical humiliation in a public place (rotten food thrown). "
            "Fines are the most common punishment of all — coin to the "
            "noble, or split with the injured party."
        ),
    ),
    _E(
        title="Duels: Outside the Law",
        text=(
            "Duels resolve disputes outside the formal legal system. They "
            "may be fought between the disputants directly, or by proxy "
            "when a party cannot fight — though it is poor form for a "
            "known fighter (a knight, say) to proxy, and reputation "
            "suffers for it. Both parties swear an oath to the terms — "
            "yield or death — before combat begins, and are bound under "
            "law: kill an opponent who yielded and you will be charged "
            "with murder. A neutral JUDGE oversees the duel and arbitrates "
            "the victor. Nobles and Highfolk may duel freely; Commonfolk "
            "must seek a Lord's permission first. Breaking a duel's terms "
            "is treated as oath-breaking and is itself a crime."
        ),
    ),
])
