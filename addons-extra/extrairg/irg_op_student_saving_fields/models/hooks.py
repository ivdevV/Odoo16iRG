def pre_init_hook(cr, registry):
        cr.execute('CREATE TABLE temp_universities (name VARCHAR(255);INSERT INTO temp_universities select distinct university_from from res_partner;
                   ALTER TABLE op_student'
                   'ADD COLUMN x_univer_backup character varying;')
        cr.execute('INSERT INTO op_student '
               'SET x_univer_backup valuesselect;')
    # in the installation the column phone is dropped

    def post_init_hook(cr, registry):
        partners = env['res.partner'].search([])
        for partner in partners:
            if partner.new_column:
                #do something
        cr.execute('select new_column from res_partner')
