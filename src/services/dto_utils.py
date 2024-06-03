from typing import Callable, Union
from pydantic import BaseModel
from sqlalchemy.orm.attributes import InstrumentedAttribute

from services.exceptions import AppException


def update_changed_attributes(current: InstrumentedAttribute, new: BaseModel, allowed_attributes: list[Union[InstrumentedAttribute, tuple[InstrumentedAttribute, list[InstrumentedAttribute]]]]):
	# For each attribute in "allowed_attributes", check if that field has been set in "new" using __fields_set__.
	# If it has, update the corresponding field in "current" with the value from "new":
	changes_made = False

	if current is None or new is None:
		return False

	for attribute in allowed_attributes:
		# If the attribute is a tuple, it means that it is a nested attribute, and we need to recurse:
		if isinstance(attribute, tuple):
			key = attribute[0].key

			nested_current = getattr(current, key)
			nested_new = getattr(new, key)
			nested_allowed_attributes = attribute[1]

			# # The nested attributes should be lists of attributes
			if not isinstance(nested_allowed_attributes, list):
				raise AppException(f"Nested allowed attributes must be a list of attributes, which {key} doesn't have.")

			if nested_new is None:
				setattr(current, key, None)
			else:
				setattr(current, key, nested_current)

			update_changed_attributes(nested_current, nested_new, nested_allowed_attributes)
			
		else:
			if attribute.key in new.__fields_set__:
				current_value = getattr(current, attribute.key)

				if hasattr(attribute.property, "uselist"):
					# The attribute is a list, so we need to recurse, somehow:
					print("Me list")
				else:
					new_value = getattr(new, attribute.key)
					if new_value != current_value:
						changes_made = True
						setattr(current, attribute.key, new_value)
		
	return changes_made

def update_relation_list(
	current: InstrumentedAttribute,
	new_ids: list[int],
	relation_field: InstrumentedAttribute,
	relation_id_field: InstrumentedAttribute,
	create_relation: Callable[[int], InstrumentedAttribute]
):
	# The list of relations on the 'current' object is updated to match the list of IDs in 'new_ids':
	# 1. Removes any relations that are not in 'new_ids'
	# 2: Creates new relations that are in 'new_ids', but not in the current list of relations


	
	if not hasattr(current, "id"):
		raise AppException(f"update_relation_list can only be used with models that have an 'id' field.")
	
	new_ids_set = set(new_ids)
	relations: list = getattr(current, relation_field.key)

	# Return false if IDs in new_ids are equal to IDs in the current list of relations
	current_ids_set = set([getattr(relation, relation_id_field.key) for relation in relations])
	if current_ids_set == new_ids_set:
		return False

	# Remove any relations that are not in the new list of IDs:
	for relation in relations:
		if getattr(relation, relation_id_field.key) not in new_ids_set:
			relations.remove(relation)
	
	# Add any relations that are in the new list of IDs but not in the current list of relations:
	missing_ids = new_ids_set - set([getattr(relation, relation_id_field.key) for relation in relations])
	for missing_id in missing_ids:
		relations.append(create_relation(missing_id))
	
	return True
	