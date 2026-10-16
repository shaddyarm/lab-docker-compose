CREATE TABLE books (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title varchar(150) NOT NULL,
    author varchar(120) NOT NULL,
    is_read boolean NOT NULL DEFAULT false
);

INSERT INTO books (title, author, is_read) VALUES
    ('Мастер и Маргарита', 'Михаил Булгаков', true),
    ('Преступление и наказание', 'Фёдор Достоевский', true),
    ('Евгений Онегин', 'Александр Пушкин', false),
    ('Война и мир', 'Лев Толстой', false),
    ('Отцы и дети', 'Иван Тургенев', true),
    ('Двенадцать стульев', 'Илья Ильф и Евгений Петров', false);
