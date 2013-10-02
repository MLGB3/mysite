/* Get rid of a couple of typos from the original data */

update books_evidence
set evidence_description = 'unknown'
where evidence_description = 'unknow';

update books_evidence set evidence_description =
'Evidence from marginalia, and from an ex-libris inscription or note of gift'
where evidence_description =
'Evidence from mmarginalia, and from an ex-libris inscription or note of gift';

