======================================
Repair Tariff Fast Duplication – Erria
======================================

* Makes default Odoo Duplicate action not copy Repair Tariff Lines with the duplicated Tariff
* Adds button for copying lines from one tariff to another through SQL trigger for users of the *Repair / Manager* group
    * This circumvents lots of Odoo logic and checks to be more memory- and time-efficient
    * The SQL works for database structure valid on 05/03/2020. If fields are added to (or removed from) models *repair.tariff.line* or *tariff.line.material*, the SQL needs to be changed in this extension, otherwise the fields' data wouldn't be copied on Tariff duplication.
        * The duplication function checks the fields and will raise an error with a short explanation if the fields were changed.
    * The duplication can take a long time (typically about 10 minutes for 500,000 tariff lines in the testing environment). If the page that started it is closed, it won't stop, and won't give any notification when the lines are copied. If this happens and you are unsure whether the copying finished or not, please check the target tariff to see if the new lines are present or not yet. The new lines only appear after the whole operation has finished. If you are still unsure, contact support.
        * The **only way** to stop the duplication once started is to have the server administrator restart the *postgresql* service or the server itself. Restarting the Odoo service will *not* affect the process.
        * Support can check logs to see if the process has finished or not. Please give them an approximate time when you started the copying.
* Adds technical field *origin_id* to Repair Tariff Line to assist with its duplication. These fields are emptied after the duplication process finishes.
* Adds duplicate check to Repair Tariff Lines
* On change of Repair Tariff's STS Value, the lines are recalculated by SQL and only when the tariff is saved.

Contributors:
=============

Lukáš Halda:
------------

* Created
