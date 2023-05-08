--------INITIALIZE AT ADDON INSTALL / UPGRADE-----------------------------------
-------- CREATE TABLES ---------------------------------------------------------
DROP TABLE IF EXISTS public.__temp_repair_tariff_line_material_dup;
CREATE UNLOGGED TABLE public.__temp_repair_tariff_line_material_dup
(
    id integer NOT NULL PRIMARY KEY, -- DEFAULT nextval('__temp_repair_tariff_line_material_dup_id_seq'::regclass),
    tariff_line_id integer NOT NULL,
    name character varying COLLATE pg_catalog."default",
    product_id integer,
    quantity double precision,
    uom_id integer NOT NULL,
    create_uid integer,
    create_date timestamp without time zone,
    write_uid integer,
    write_date timestamp without time zone
    -- ,
    -- CONSTRAINT __temp_repair_tariff_line_material_dup_pkey PRIMARY KEY (id),
    -- CONSTRAINT repair_tariff_line_material_duplication_tem_tariff_line_id_fkey FOREIGN KEY (tariff_line_id)
    --     REFERENCES public.repair_tariff_line (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE CASCADE,
    -- CONSTRAINT repair_tariff_line_material_duplication_tempora_create_uid_fkey FOREIGN KEY (create_uid)
    --     REFERENCES public.res_users (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT repair_tariff_line_material_duplication_tempora_product_id_fkey FOREIGN KEY (product_id)
    --     REFERENCES public.product_product (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT repair_tariff_line_material_duplication_temporar_write_uid_fkey FOREIGN KEY (write_uid)
    --     REFERENCES public.res_users (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT repair_tariff_line_material_duplication_temporary_l_uom_id_fkey FOREIGN KEY (uom_id)
    --     REFERENCES public.uom_uom (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

-- ALTER TABLE public.__temp_repair_tariff_line_material_dup
--     OWNER to lukas;
COMMENT ON TABLE public.__temp_repair_tariff_line_material_dup
    IS 'Repair Tariff Line Material - temporary duplication table';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.tariff_line_id
    IS 'Tariff Line';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.name
    IS 'Name';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.product_id
    IS 'Product';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.quantity
    IS 'Quantity';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.uom_id
    IS 'Uom';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.create_uid
    IS 'Created by';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.create_date
    IS 'Created on';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.write_uid
    IS 'Last Updated by';
COMMENT ON COLUMN public.__temp_repair_tariff_line_material_dup.write_date
    IS 'Last Updated on';
-- Index: __temp_repair_tariff_line_material_dup_tariff_
-- DROP INDEX public.__temp_repair_tariff_line_material_dup_tariff_;
-- CREATE INDEX __temp_repair_tariff_line_material_dup_tariff_
--     ON public.__temp_repair_tariff_line_material_dup USING btree
--     (tariff_line_id ASC NULLS LAST)
--     TABLESPACE pg_default;

DROP TABLE IF EXISTS public.__temp_repair_tariff_line_dup;
CREATE UNLOGGED TABLE public.__temp_repair_tariff_line_dup
(
    id integer NOT NULL PRIMARY KEY, -- DEFAULT nextval('__temp_repair_tariff_line_dup_id_seq'::regclass),
    origin_id integer,
    tariff_id integer NOT NULL,
    name character varying COLLATE pg_catalog."default",
    component_id integer NOT NULL,
    damage_type integer NOT NULL,
    labour_price double precision,
    length double precision NOT NULL,
    location_id integer NOT NULL,
    material_price double precision,
    mode_id integer,
    price_subtotal double precision,
    quantity double precision NOT NULL,
    repair_code character varying COLLATE pg_catalog."default",
    repair_type_id integer NOT NULL,
    sts double precision NOT NULL,
    width double precision NOT NULL,
    create_uid integer,
    create_date timestamp without time zone,
    write_uid integer,
    write_date timestamp without time zone
    -- ,
    -- CONSTRAINT __temp_repair_tariff_line_dup_pkey PRIMARY KEY (id),
    -- CONSTRAINT repair_tariff_line_duplication_temporary_li_repair_type_id_fkey FOREIGN KEY (repair_type_id)
    --     REFERENCES public.repair_types (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT repair_tariff_line_duplication_temporary_line_component_id_fkey FOREIGN KEY (component_id)
    --     REFERENCES public.repair_component (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT __temp_repair_tariff_line_dup_create_uid_fkey FOREIGN KEY (create_uid)
    --     REFERENCES public.res_users (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT __temp_repair_tariff_line_dup_damage_type_fkey FOREIGN KEY (damage_type)
    --     REFERENCES public.damage_type (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT __temp_repair_tariff_line_dup_location_id_fkey FOREIGN KEY (location_id)
    --     REFERENCES public.repair_location (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT __temp_repair_tariff_line_dup_mode_id_fkey FOREIGN KEY (mode_id)
    --     REFERENCES public.repair_mode (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT __temp_repair_tariff_line_dup_origin_id_fkey FOREIGN KEY (origin_id)
    --     REFERENCES public.repair_tariff_line (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL,
    -- CONSTRAINT __temp_repair_tariff_line_dup_tariff_id_fkey FOREIGN KEY (tariff_id)
    --     REFERENCES public.repair_tariff (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE CASCADE,
    -- CONSTRAINT __temp_repair_tariff_line_dup_write_uid_fkey FOREIGN KEY (write_uid)
    --     REFERENCES public.res_users (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE SET NULL
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

-- ALTER TABLE public.__temp_repair_tariff_line_dup
--     OWNER to lukas;
COMMENT ON TABLE public.__temp_repair_tariff_line_dup
    IS 'Repair Tariff Line - temporary duplication table';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.origin_id
    IS 'Origin';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.tariff_id
    IS 'Tariff';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.name
    IS 'Combined Code';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.component_id
    IS 'Component';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.damage_type
    IS 'Damage';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.labour_price
    IS 'Labour Price';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.length
    IS 'Length';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.location_id
    IS 'Location';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.material_price
    IS 'Material Price';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.mode_id
    IS 'Mode';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.price_subtotal
    IS 'Price Before Taxes';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.quantity
    IS 'Quantity';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.repair_code
    IS 'Customer Repair Code';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.repair_type_id
    IS 'Repair';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.sts
    IS 'STS';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.width
    IS 'Width';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.create_uid
    IS 'Created by';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.create_date
    IS 'Created on';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.write_uid
    IS 'Last Updated by';
COMMENT ON COLUMN public.__temp_repair_tariff_line_dup.write_date
    IS 'Last Updated on';
-- -- Index: __temp_repair_tariff_line_dup_tariff_id_index
-- DROP INDEX public.__temp_repair_tariff_line_dup_tariff_id_index;
-- CREATE INDEX __temp_repair_tariff_line_dup_tariff_id_index
--     ON public.__temp_repair_tariff_line_dup USING btree
--     (tariff_id ASC NULLS LAST)
--     TABLESPACE pg_default;

DROP TABLE IF EXISTS public.__temp_repair_tariff_line_tax_rel_dup;
CREATE UNLOGGED TABLE public.__temp_repair_tariff_line_tax_rel_dup
(
    tariff_line_id integer NOT NULL,
    tax_id integer NOT NULL
    -- ,
    -- CONSTRAINT __temp_repair_tariff_line_tax_rel_dup_tariff_line_id_tax_id_key UNIQUE (tariff_line_id, tax_id)-- ,
    -- CONSTRAINT __temp_repair_tariff_line_tax_rel_dup_tariff_line_id_fkey FOREIGN KEY (tariff_line_id)
    --     REFERENCES public.repair_tariff_line (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE CASCADE,
    -- CONSTRAINT __temp_repair_tariff_line_tax_rel_dup_tax_id_fkey FOREIGN KEY (tax_id)
    --     REFERENCES public.account_tax (id) MATCH SIMPLE
    --     ON UPDATE NO ACTION
    --     ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

-- ALTER TABLE public.__temp_repair_tariff_line_tax_rel_dup
--     OWNER to lukas;
COMMENT ON TABLE public.__temp_repair_tariff_line_tax_rel_dup
    IS 'RELATION BETWEEN repair_tariff_line AND account_tax';
-- -- Index: __temp_repair_tariff_line_tax_rel_dup_tariff_line_id_idx
-- DROP INDEX public.__temp_repair_tariff_line_tax_rel_dup_tariff_line_id_idx;
-- CREATE INDEX __temp_repair_tariff_line_tax_rel_dup_tariff_line_id_idx
--     ON public.__temp_repair_tariff_line_tax_rel_dup USING btree
--     (tariff_line_id ASC NULLS LAST)
--     TABLESPACE pg_default;
-- -- Index: __temp_repair_tariff_line_tax_rel_dup_tax_id_idx
-- DROP INDEX public.__temp_repair_tariff_line_tax_rel_dup_tax_id_idx;
-- CREATE INDEX __temp_repair_tariff_line_tax_rel_dup_tax_id_idx
--     ON public.__temp_repair_tariff_line_tax_rel_dup USING btree
--     (tax_id ASC NULLS LAST)
--     TABLESPACE pg_default;


ALTER TABLE public.__temp_repair_tariff_line_material_dup SET (
  autovacuum_enabled = false, toast.autovacuum_enabled = false
);

ALTER TABLE public.__temp_repair_tariff_line_dup SET (
  autovacuum_enabled = false, toast.autovacuum_enabled = false
);

ALTER TABLE public.__temp_repair_tariff_line_tax_rel_dup SET (
  autovacuum_enabled = false, toast.autovacuum_enabled = false
);

--------LET US CREATE THE FUNCTION FIRST BEFORE CALLING IT WITH THE TRIGGER-----
CREATE OR REPLACE FUNCTION repair_tariff_line_duplication()
    RETURNS "trigger" AS
    $BODY$
    BEGIN
        -- Copy new lines to a temporary table --
        TRUNCATE TABLE __temp_repair_tariff_line_dup;
        INSERT INTO __temp_repair_tariff_line_dup (
            id, tariff_id, name, component_id, location_id, damage_type, repair_type_id, length,
            width, repair_code, quantity, sts, labour_price, material_price, price_subtotal,
            create_uid, create_date, write_uid, write_date, mode_id, origin_id
            )
        SELECT id, NEW.target_id "tariff_id", name, component_id, location_id, damage_type, 
            repair_type_id, length, width, repair_code, quantity, sts,
            sts * NEW.target_sts_value "labour_price", material_price,
            sts * NEW.target_sts_value + material_price "price_subtotal",
            NEW.create_uid "create_uid", NEW.create_date "create_date",
            NEW.write_uid "write_uid", NEW.write_date "write_date", mode_id, id "origin_id"
        FROM repair_tariff_line
        WHERE tariff_id = NEW.source_id;

        -- Copy temporary lines to the lines table -> insert on the source table circumvented --
        INSERT INTO repair_tariff_line (
            tariff_id, name, component_id, location_id, damage_type, repair_type_id, length,
            width, repair_code, quantity, sts, labour_price, material_price, price_subtotal,
            create_uid, create_date, write_uid, write_date, mode_id, origin_id
        )
        SELECT tariff_id, name, component_id, location_id, damage_type, 
            repair_type_id, length, width, repair_code, quantity, sts, labour_price, 
            material_price, price_subtotal, create_uid, create_date, write_uid, write_date,
            mode_id, origin_id
        FROM __temp_repair_tariff_line_dup;
        -- WHERE tariff_id = NEW.target_id;
        TRUNCATE TABLE __temp_repair_tariff_line_dup;

        -- Copy material lines to the temporary table --
        TRUNCATE TABLE __temp_repair_tariff_line_material_dup;
        INSERT INTO __temp_repair_tariff_line_material_dup (
            id, tariff_line_id, name, product_id, quantity, uom_id,
            create_uid, create_date, write_uid, write_date)
        SELECT m.id, ln.id "tariff_line_id", m.name, m.product_id, m.quantity, m.uom_id,
            NEW.create_uid, NEW.create_date, NEW.write_uid, NEW.write_date
        FROM tariff_line_material m
        LEFT JOIN repair_tariff_line ln ON ln.origin_id = m.tariff_line_id
        WHERE ln.tariff_id = NEW.target_id;

        -- Copy temporary material lines to the material lines table --
        INSERT INTO tariff_line_material (tariff_line_id, name, product_id, quantity, uom_id,
            create_uid, create_date, write_uid, write_date
        )
        SELECT tariff_line_id, name, product_id, quantity, uom_id,
            create_uid, create_date, write_uid, write_date
        FROM __temp_repair_tariff_line_material_dup;
        /*WHERE tariff_line_id in (
            SELECT id FROM repair_tariff_line
            WHERE tariff_id = NEW.target_id AND origin_id IS NOT NULL
        );*/
        TRUNCATE TABLE __temp_repair_tariff_line_material_dup;

        -- Copy tax IDs to the temporary table --
        TRUNCATE TABLE __temp_repair_tariff_line_tax_rel_dup;
        INSERT INTO __temp_repair_tariff_line_tax_rel_dup (tariff_line_id, tax_id)
        SELECT ln.id "tariff_line_id", t.tax_id
        FROM tariff_line_tax_rel t
        LEFT JOIN repair_tariff_line ln ON ln.origin_id = t.tariff_line_id
        WHERE ln.tariff_id = NEW.target_id;

        -- Copy temporary tax IDs to the relation table --
        INSERT INTO tariff_line_tax_rel (tariff_line_id, tax_id)
        SELECT * FROM __temp_repair_tariff_line_tax_rel_dup;
        /*WHERE tariff_line_id in (
            SELECT id FROM repair_tariff_line
            WHERE tariff_id = NEW.target_id AND origin_id IS NOT NULL
        );*/
        TRUNCATE TABLE __temp_repair_tariff_line_tax_rel_dup;

        -- Clean-up:
        ---- Delete the duplication trigger
        ---- (would prevent deletion of source or target without Repair: Manager rights)
        DELETE FROM repair_tariff_line_duplication
        WHERE id = NEW.id;
        ---- Clear origin_id from the copied lines
        ---- (would cause errors or duplicate duplication on next copying from the same source)
        UPDATE repair_tariff_line
        SET origin_id = NULL
        WHERE tariff_id = NEW.target_id;

        RETURN NEW;
    END;
    $BODY$
        LANGUAGE 'plpgsql' SECURITY DEFINER;
-------- TRIGGER -------------------------------------
DROP TRIGGER IF EXISTS trigger_tarif_duplication_detect ON repair_tariff_line_duplication;
CREATE TRIGGER trigger_tarif_duplication_detect
 AFTER INSERT ON repair_tariff_line_duplication
 FOR EACH ROW ------- THIS MEANS PER INSERT PER LINE
EXECUTE PROCEDURE repair_tariff_line_duplication();
