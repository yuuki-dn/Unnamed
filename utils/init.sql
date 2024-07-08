CREATE TABLE IF NOT EXISTS `guilds` (
    `guild_id` BIGINT NOT NULL UNIQUE,
    `wordchain_channel_id` BIGINT DEFAULT NULL,
    PRIMARY KEY(`guild_id`)
);

CREATE TABLE IF NOT EXISTS `reaction_roles` (
    `id` BIGINT NOT NULL AUTO_INCREMENT UNIQUE,
    `guild_id` BIGINT NOT NULL,
    `message_id` BIGINT NOT NULL,
    `role_id` BIGINT NOT NULL,
    `emoji` VARCHAR(255) NOT NULL,
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `member_xp` (
    `user_id` BIGINT NOT NULL UNIQUE,
    `guild_id` BIGINT NOT NULL,
    `xp` BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY(`user_id`)
);

CREATE TABLE IF NOT EXISTS `guild_level_role` (
    `guild_id` BIGINT NOT NULL UNIQUE,
    `level` BIGINT NOT NULL,
    `role_id` BIGINT NOT NULL,
    PRIMARY KEY(`guild_id`)
);