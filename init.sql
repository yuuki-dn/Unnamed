CREATE TABLE IF NOT EXISTS `guilds` (
    `guild_id` BIGINT NOT NULL UNIQUE,
    `wordchain_channel_id` BIGINT DEFAULT NULL,
    PRIMARY KEY(`guild_id`)
);

CREATE TABLE IF NOT EXISTS `reaction_role_messages` (
    `id` BIGINT NOT NULL AUTO_INCREMENT UNIQUE,
    `guild_id` BIGINT NOT NULL,
    `message_id` BIGINT NOT NULL,
    `emoji` VARCHAR(45) NOT NULL,
    `role_id` BIGINT NOT NULL,
    PRIMARY KEY(`id`),
    CONSTRAINT `fk_guild_id`
        FOREIGN KEY (`guild_id`)
        REFERENCES `guilds` (`guild_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX `idx_guild_id` ON `reaction_role_messages` (`guild_id`);
CREATE INDEX `idx_message_id` ON `reaction_role_messages` (`message_id`);

CREATE TABLE IF NOT EXISTS `member_xp` (
    `user_id` BIGINT NOT NULL UNIQUE,
    `xp` BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY(`user_id`)
);