# -*- coding: utf-8 -*-

import datetime

import pytest

from sqlalchemy.orm import joinedload
from sqlalchemy_filters.exceptions import BadSortFormat, BadSpec, FieldNotFound
from sqlalchemy_filters.sorting import apply_sort
from test import error_value
from test.models import Foo, Bar, Qux


@pytest.fixture
def multiple_foos_inserted(session, multiple_bars_inserted):
    foo_1 = Foo(id=1, bar_id=1, name='name_1', count=1)
    foo_2 = Foo(id=2, bar_id=2, name='name_2', count=1)
    foo_3 = Foo(id=3, bar_id=3, name='name_1', count=1)
    foo_4 = Foo(id=4, bar_id=4, name='name_4', count=1)
    foo_5 = Foo(id=5, bar_id=5, name='name_1', count=2)
    foo_6 = Foo(id=6, bar_id=6, name='name_4', count=2)
    foo_7 = Foo(id=7, bar_id=7, name='name_1', count=2)
    foo_8 = Foo(id=8, bar_id=8, name='name_5', count=2)
    session.add_all(
        [foo_1, foo_2, foo_3, foo_4, foo_5, foo_6, foo_7, foo_8]
    )
    session.commit()


@pytest.fixture
def multiple_bars_inserted(session):
    bar_1 = Bar(id=1, name='name_1', count=5)
    bar_2 = Bar(id=2, name='name_2', count=10)
    bar_3 = Bar(id=3, name='name_1', count=None)
    bar_4 = Bar(id=4, name='name_4', count=12)
    bar_5 = Bar(id=5, name='name_1', count=2)
    bar_6 = Bar(id=6, name='name_4', count=15)
    bar_7 = Bar(id=7, name='name_1', count=2)
    bar_8 = Bar(id=8, name='name_5', count=1)
    session.add_all(
        [bar_1, bar_2, bar_3, bar_4, bar_5, bar_6, bar_7, bar_8]
    )
    session.commit()


class TestSortNotApplied(object):

    def test_no_sort_provided(self, session):
        query = session.query(Bar)
        order_by = []

        filtered_query = apply_sort(query, order_by)

        assert query == filtered_query

    @pytest.mark.parametrize('sort', ['some text', 1, []])
    def test_wrong_sort_format(self, session, sort):
        query = session.query(Bar)
        order_by = [sort]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = 'Sort spec `{}` should be a dictionary.'.format(sort)
        assert expected_error == error_value(err)

    def test_field_not_provided(self, session):
        query = session.query(Bar)
        order_by = [{'direction': 'asc'}]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = '`field` and `direction` are mandatory attributes.'
        assert expected_error == error_value(err)

    def test_invalid_field(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'invalid_field', 'direction': 'asc'}]

        with pytest.raises(FieldNotFound) as err:
            apply_sort(query, order_by)

        expected_error = (
            "Model <class 'test.models.Bar'> has no column `invalid_field`."
        )
        assert expected_error == error_value(err)

    def test_direction_not_provided(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name'}]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = '`field` and `direction` are mandatory attributes.'
        assert expected_error == error_value(err)

    def test_invalid_direction(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name', 'direction': 'invalid_direction'}]

        with pytest.raises(BadSortFormat) as err:
            apply_sort(query, order_by)

        expected_error = 'Direction `invalid_direction` not valid.'
        assert expected_error == error_value(err)


class TestSortApplied(object):

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_single_sort_field_asc(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name', 'direction': 'asc'}]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 1
        assert result[1].id == 3
        assert result[2].id == 5
        assert result[3].id == 7
        assert result[4].id == 2
        assert result[5].id == 4
        assert result[6].id == 6
        assert result[7].id == 8

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_single_sort_field_desc(self, session):
        query = session.query(Bar)
        order_by = [{'field': 'name', 'direction': 'desc'}]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 8
        assert result[1].id == 4
        assert result[2].id == 6
        assert result[3].id == 2
        assert result[4].id == 1
        assert result[5].id == 3
        assert result[6].id == 5
        assert result[7].id == 7

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_multiple_sort_fields(self, session):
        query = session.query(Bar)
        order_by = [
            {'field': 'name', 'direction': 'asc'},
            {'field': 'count', 'direction': 'desc'},
            {'field': 'id', 'direction': 'desc'},
        ]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 1
        assert result[1].id == 7
        assert result[2].id == 5
        assert result[3].id == 3
        assert result[4].id == 2
        assert result[5].id == 6
        assert result[6].id == 4
        assert result[7].id == 8

    def test_multiple_models(self, session):

        bar_1 = Bar(id=1, name='name_1', count=5)
        bar_2 = Bar(id=2, name='name_2', count=10)
        bar_3 = Bar(id=3, name='name_1', count=None)
        bar_4 = Bar(id=4, name='name_1', count=12)

        qux_1 = Qux(
            id=1, name='name_1', count=5,
            created_at=datetime.date(2016, 7, 12),
            execution_time=datetime.datetime(2016, 7, 12, 1, 5, 9)
        )
        qux_2 = Qux(
            id=2, name='name_2', count=10,
            created_at=datetime.date(2016, 7, 13),
            execution_time=datetime.datetime(2016, 7, 13, 2, 5, 9)
        )
        qux_3 = Qux(
            id=3, name='name_1', count=None,
            created_at=None, execution_time=None
        )
        qux_4 = Qux(
            id=4, name='name_1', count=15,
            created_at=datetime.date(2016, 7, 14),
            execution_time=datetime.datetime(2016, 7, 14, 3, 5, 9)
        )

        session.add_all(
            [bar_1, bar_2, bar_3, bar_4, qux_1, qux_2, qux_3, qux_4]
        )
        session.commit()

        query = session.query(Bar).join(Qux, Bar.id == Qux.id)
        order_by = [
            {'model': 'Bar', 'field': 'name', 'direction': 'asc'},
            {'model': 'Qux', 'field': 'count', 'direction': 'asc'}
        ]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 4
        assert result[0].id == 3
        assert result[1].id == 1
        assert result[2].id == 4
        assert result[3].id == 2

    @pytest.mark.usefixtures('multiple_bars_inserted')
    def test_a_single_dict_can_be_supplied_as_sort_spec(self, session):
        query = session.query(Bar)
        sort_spec = {'field': 'name', 'direction': 'desc'}

        sorted_query = apply_sort(query, sort_spec)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 8
        assert result[1].id == 4
        assert result[2].id == 6
        assert result[3].id == 2
        assert result[4].id == 1
        assert result[5].id == 3
        assert result[6].id == 5
        assert result[7].id == 7


class TestAutoJoin:

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_auto_join(self, session):

        query = session.query(Foo)
        order_by = [
            {'field': 'count', 'direction': 'desc'},
            {'model': 'Bar', 'field': 'name', 'direction': 'asc'},
            {'field': 'id', 'direction': 'asc'},
        ]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 5
        assert result[1].id == 7
        assert result[2].id == 6
        assert result[3].id == 8
        assert result[4].id == 1
        assert result[5].id == 3
        assert result[6].id == 2
        assert result[7].id == 4

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_noop_if_query_contains_named_models(self, session):

        query = session.query(Foo).join(Bar)
        order_by = [
            {'model': 'Foo', 'field': 'count', 'direction': 'desc'},
            {'model': 'Bar', 'field': 'name', 'direction': 'asc'},
            {'model': 'Foo', 'field': 'id', 'direction': 'asc'},
        ]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 5
        assert result[1].id == 7
        assert result[2].id == 6
        assert result[3].id == 8
        assert result[4].id == 1
        assert result[5].id == 3
        assert result[6].id == 2
        assert result[7].id == 4

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_auto_join_to_invalid_model(self, session):

        query = session.query(Foo)
        order_by = [
            {'model': 'Foo', 'field': 'count', 'direction': 'desc'},
            {'model': 'Bar', 'field': 'name', 'direction': 'asc'},
            {'model': 'Qux', 'field': 'count', 'direction': 'asc'}
        ]

        with pytest.raises(BadSpec) as err:
            apply_sort(query, order_by)

        assert 'The query does not contain model `Qux`.' == err.value.args[0]

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_ambiguous_query(self, session):

        query = session.query(Foo).join(Bar)
        order_by = [
            {'field': 'count', 'direction': 'asc'},  # ambiguous
            {'model': 'Bar', 'field': 'name', 'direction': 'desc'},
        ]
        with pytest.raises(BadSpec) as err:
            apply_sort(query, order_by)

        assert 'Ambiguous spec. Please specify a model.' == err.value.args[0]

    @pytest.mark.usefixtures('multiple_foos_inserted')
    def test_eager_load(self, session):

        # behaves as if the joinedload wasn't present
        query = session.query(Foo).options(joinedload(Foo.bar))
        order_by = [
            {'field': 'count', 'direction': 'desc'},
            {'model': 'Bar', 'field': 'name', 'direction': 'asc'},
            {'field': 'id', 'direction': 'asc'},
        ]

        sorted_query = apply_sort(query, order_by)
        result = sorted_query.all()

        assert len(result) == 8
        assert result[0].id == 5
        assert result[1].id == 7
        assert result[2].id == 6
        assert result[3].id == 8
        assert result[4].id == 1
        assert result[5].id == 3
        assert result[6].id == 2
        assert result[7].id == 4
