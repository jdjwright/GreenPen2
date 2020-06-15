from django import forms


class TreeSelectMultiple(forms.CheckboxSelectMultiple):

    class Media:
        js = ('js/mptt_collapse_list_view.js',)

    template_name = 'GreenPen/treeselectmultiple.html'
    option_template_name = 'GreenPen/treecheckbox.html'
    level_indicator = ''

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        initial_dict = super().create_option(name, value, label, selected, index, subindex, attrs)

        related_mptt_item = self.choices.queryset.get(pk=initial_dict['value'])
        initial_dict['has_children'] = not related_mptt_item.is_leaf_node()
        initial_dict['level'] = related_mptt_item.level

        def check_if_needs_closing(item_to_check):
            if not item_to_check.get_next_sibling():
                return True
            return False
        tags_to_close = []

        while True:
            if not check_if_needs_closing(related_mptt_item):
                break

            else:
                if related_mptt_item.is_child_node():
                    related_mptt_item = related_mptt_item.parent
                    tags_to_close.append('close')
                else:
                    break
        # Check if parent was last item

        initial_dict['tags_to_close'] = tags_to_close

        return initial_dict


class TreeSelect(forms.RadioSelect):

    class Media:
        js = ('js/mptt_radio_collapse_list_view.js',)

    template_name = 'GreenPen/treeselectmultiple.html'
    option_template_name = 'Greenpen/treecheckbox.html'
    level_indicator = ''

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        initial_dict = super().create_option(name, value, label, selected, index, subindex, attrs)

        if(isinstance(initial_dict['value'], int)):
            related_mptt_item = self.choices.queryset.get(pk=initial_dict['value'])
            initial_dict['has_children'] = not related_mptt_item.is_leaf_node()
            initial_dict['level'] = related_mptt_item.level

            def check_if_needs_closing(item_to_check):
                if not item_to_check.get_next_sibling():
                    return True
                return False
            tags_to_close = []

            while True:
                if not check_if_needs_closing(related_mptt_item):
                    break

                else:
                    if related_mptt_item.is_child_node():
                        related_mptt_item = related_mptt_item.parent
                        tags_to_close.append('close')
                    else:
                        break
            # Check if parent was last item

            initial_dict['tags_to_close'] = tags_to_close

        return initial_dict


